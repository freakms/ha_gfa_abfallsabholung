"""Data coordinator for GFA Abfallkalender."""
import logging
from datetime import datetime, date, timedelta
from typing import Any

from icalendar import Calendar
import recurring_ical_events

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GFALueneburgAPI
from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    WASTE_TYPE_MAPPINGS,
    CONF_CITY,
    CONF_STREET,
    CONF_HOUSE_NUMBER,
    CONF_ICS_URL,
)

_LOGGER = logging.getLogger(__name__)


class GFADataCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch and manage waste calendar data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config: dict[str, Any],
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self._config = config
        self._api = GFALueneburgAPI()
        self._calendar: Calendar | None = None
        self._events: list[dict[str, Any]] = []
        
        # Check if we have address-based config or ICS URL
        self._use_api = CONF_CITY in config

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from ICS calendar."""
        try:
            if self._use_api:
                # Fetch ICS using the API with address
                ics_content = await self._api.get_ics_calendar(
                    self._config[CONF_CITY],
                    self._config[CONF_STREET],
                    self._config[CONF_HOUSE_NUMBER],
                )
            else:
                # Fetch ICS from URL
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        self._config[CONF_ICS_URL], timeout=30
                    ) as response:
                        if response.status != 200:
                            raise UpdateFailed(
                                f"Error fetching calendar: HTTP {response.status}"
                            )
                        ics_content = await response.text()

            # Parse calendar
            self._calendar = Calendar.from_ical(ics_content)

            # Get events for the next 60 days
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=60)

            events = recurring_ical_events.of(self._calendar).between(
                start_date, end_date
            )

            self._events = []
            for event in events:
                event_data = self._parse_event(event)
                if event_data:
                    self._events.append(event_data)

            # Sort events by date
            self._events.sort(key=lambda x: x["date"])

            # Group events by waste type
            waste_data = {}
            for event in self._events:
                waste_type = event.get("waste_type", "unknown")
                if waste_type not in waste_data:
                    waste_data[waste_type] = []
                waste_data[waste_type].append(event)

            return {
                "events": self._events,
                "by_type": waste_data,
                "last_update": datetime.now(),
            }

        except Exception as err:
            _LOGGER.error(f"Error updating calendar data: {err}")
            raise UpdateFailed(f"Error fetching calendar: {err}") from err

    def _parse_event(self, event) -> dict[str, Any] | None:
        """Parse an ICS event into our format."""
        try:
            summary = str(event.get("SUMMARY", "")).strip()
            if not summary:
                return None

            # Get event date
            dtstart = event.get("DTSTART")
            if dtstart:
                event_date = dtstart.dt
                if isinstance(event_date, datetime):
                    event_date = event_date.date()
            else:
                return None

            # Determine waste type
            waste_type = self._detect_waste_type(summary)

            return {
                "summary": summary,
                "date": event_date,
                "waste_type": waste_type,
                "description": str(event.get("DESCRIPTION", "")),
            }
        except Exception as err:
            _LOGGER.warning(f"Error parsing event: {err}")
            return None

    def _detect_waste_type(self, summary: str) -> str:
        """Detect the waste type from the event summary."""
        summary_lower = summary.lower()

        for waste_type, keywords in WASTE_TYPE_MAPPINGS.items():
            for keyword in keywords:
                if keyword in summary_lower:
                    return waste_type

        return "unknown"

    def get_next_pickup(self, waste_type: str | None = None) -> dict[str, Any] | None:
        """Get the next pickup date."""
        today = datetime.now().date()

        for event in self._events:
            if event["date"] >= today:
                if waste_type is None or event["waste_type"] == waste_type:
                    return event

        return None

    def get_pickups_for_date(self, target_date: date) -> list[dict[str, Any]]:
        """Get all pickups for a specific date."""
        return [event for event in self._events if event["date"] == target_date]

    def get_all_waste_types(self) -> list[str]:
        """Get all waste types found in the calendar."""
        if not self.data:
            return []
        return list(self.data.get("by_type", {}).keys())

    async def async_close(self) -> None:
        """Close API session."""
        await self._api.close()
