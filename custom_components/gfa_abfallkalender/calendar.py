"""Calendar platform for GFA Abfallkalender."""
from datetime import datetime, timedelta
import logging

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, WASTE_TYPE_NAMES, WASTE_TYPE_ICONS
from .coordinator import GFADataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GFA Abfallkalender calendar."""
    coordinator: GFADataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([GFACalendarEntity(coordinator, entry)])


class GFACalendarEntity(CoordinatorEntity, CalendarEntity):
    """Calendar entity for GFA waste collection dates."""

    _attr_icon = "mdi:trash-can-outline"

    def __init__(
        self,
        coordinator: GFADataCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the calendar entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_name = "GFA Abfallkalender"

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        pickup = self.coordinator.get_next_pickup()
        if pickup:
            return CalendarEvent(
                start=pickup["date"],
                end=pickup["date"] + timedelta(days=1),
                summary=pickup["summary"],
                description=pickup.get("description", ""),
            )
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        events = []
        
        if not self.coordinator.data:
            return events

        start = start_date.date() if isinstance(start_date, datetime) else start_date
        end = end_date.date() if isinstance(end_date, datetime) else end_date

        for event_data in self.coordinator.data.get("events", []):
            event_date = event_data["date"]
            if start <= event_date <= end:
                events.append(
                    CalendarEvent(
                        start=event_date,
                        end=event_date + timedelta(days=1),
                        summary=event_data["summary"],
                        description=event_data.get("description", ""),
                    )
                )

        return events
