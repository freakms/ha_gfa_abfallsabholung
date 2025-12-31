"""Sensor platform for GFA Abfallkalender."""
from datetime import datetime
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    WASTE_TYPE_NAMES,
    WASTE_TYPE_ICONS,
)
from .coordinator import GFADataCoordinator

_LOGGER = logging.getLogger(__name__)

# Emoji mappings for waste types (for dashboard display)
WASTE_TYPE_EMOJIS = {
    "restmuell": "🗑️",
    "altpapier": "📰",
    "gelber_sack": "♻️",
    "biotonne": "🌱",
    "gruenabfall": "🌳",
    "sperrmuell": "🛋️",
    "schadstoffmobil": "☣️",
    "weihnachtsbaum": "🎄",
    "unknown": "📦",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GFA Abfallkalender sensors."""
    coordinator: GFADataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # Wait for first data fetch
    if not coordinator.data:
        await coordinator.async_refresh()

    # Create sensors for each waste type found
    entities = []
    
    # Add a general "next pickup" sensor
    entities.append(GFANextPickupSensor(coordinator, entry))
    
    # Add "next 5 pickups" sensor for dashboard
    entities.append(GFAUpcomingPickupsSensor(coordinator, entry))

    # Add sensors for each waste type
    waste_types = coordinator.get_all_waste_types()
    for waste_type in waste_types:
        entities.append(GFAWasteTypeSensor(coordinator, entry, waste_type))

    async_add_entities(entities)


class GFANextPickupSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the next waste pickup."""

    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:trash-can-outline"

    def __init__(
        self,
        coordinator: GFADataCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_next_pickup"
        self._attr_name = "GFA Nächste Abholung"

    @property
    def native_value(self):
        """Return the next pickup date."""
        pickup = self.coordinator.get_next_pickup()
        if pickup:
            return pickup["date"]
        return None

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        pickup = self.coordinator.get_next_pickup()
        if pickup:
            days_until = (pickup["date"] - datetime.now().date()).days
            return {
                "waste_type": pickup["waste_type"],
                "waste_type_name": WASTE_TYPE_NAMES.get(
                    pickup["waste_type"], pickup["summary"]
                ),
                "summary": pickup["summary"],
                "days_until": days_until,
                "is_tomorrow": days_until == 1,
                "is_today": days_until == 0,
            }
        return {}


class GFAUpcomingPickupsSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the next 5 upcoming waste pickups."""

    _attr_icon = "mdi:calendar-check"

    def __init__(
        self,
        coordinator: GFADataCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_upcoming_pickups"
        self._attr_name = "GFA Kommende Termine"

    @property
    def native_value(self):
        """Return the count of upcoming pickups."""
        if self.coordinator.data:
            events = self.coordinator.data.get("events", [])
            today = datetime.now().date()
            upcoming = [e for e in events if e["date"] >= today][:5]
            return len(upcoming)
        return 0

    @property
    def extra_state_attributes(self):
        """Return the next 5 pickups as attributes."""
        if not self.coordinator.data:
            return {}
        
        events = self.coordinator.data.get("events", [])
        today = datetime.now().date()
        upcoming = [e for e in events if e["date"] >= today][:5]
        
        attributes = {
            "pickups": [],
            "pickup_count": len(upcoming),
        }
        
        # German weekday names
        weekdays_de = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        
        for i, event in enumerate(upcoming, 1):
            waste_type = event.get("waste_type", "unknown")
            event_date = event["date"]
            days_until = (event_date - today).days
            
            # Format date nicely
            weekday = weekdays_de[event_date.weekday()]
            date_str = event_date.strftime(f"{weekday}, %d.%m.%Y")
            
            # Day description
            if days_until == 0:
                day_desc = "Heute"
            elif days_until == 1:
                day_desc = "Morgen"
            elif days_until == 2:
                day_desc = "Übermorgen"
            else:
                day_desc = f"in {days_until} Tagen"
            
            pickup_data = {
                "nummer": i,
                "datum": date_str,
                "datum_iso": event_date.isoformat(),
                "tage_bis": days_until,
                "tag_beschreibung": day_desc,
                "abfallart": waste_type,
                "abfallart_name": WASTE_TYPE_NAMES.get(waste_type, event.get("summary", waste_type)),
                "icon": WASTE_TYPE_ICONS.get(waste_type, "mdi:trash-can"),
                "emoji": WASTE_TYPE_EMOJIS.get(waste_type, "📦"),
                "beschreibung": event.get("summary", ""),
            }
            attributes["pickups"].append(pickup_data)
            
            # Also add as individual attributes for easier template access
            attributes[f"termin_{i}_datum"] = date_str
            attributes[f"termin_{i}_typ"] = WASTE_TYPE_NAMES.get(waste_type, waste_type)
            attributes[f"termin_{i}_emoji"] = WASTE_TYPE_EMOJIS.get(waste_type, "📦")
            attributes[f"termin_{i}_tage"] = days_until
            attributes[f"termin_{i}_icon"] = WASTE_TYPE_ICONS.get(waste_type, "mdi:trash-can")
        
        return attributes


class GFAWasteTypeSensor(CoordinatorEntity, SensorEntity):
    """Sensor for a specific waste type."""

    _attr_device_class = SensorDeviceClass.DATE

    def __init__(
        self,
        coordinator: GFADataCoordinator,
        entry: ConfigEntry,
        waste_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._waste_type = waste_type
        self._attr_unique_id = f"{entry.entry_id}_{waste_type}"
        self._attr_name = f"GFA {WASTE_TYPE_NAMES.get(waste_type, waste_type)}"
        self._attr_icon = WASTE_TYPE_ICONS.get(waste_type, "mdi:trash-can")

    @property
    def native_value(self):
        """Return the next pickup date for this waste type."""
        pickup = self.coordinator.get_next_pickup(self._waste_type)
        if pickup:
            return pickup["date"]
        return None

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        pickup = self.coordinator.get_next_pickup(self._waste_type)
        if pickup:
            days_until = (pickup["date"] - datetime.now().date()).days
            return {
                "summary": pickup["summary"],
                "days_until": days_until,
                "is_tomorrow": days_until == 1,
                "is_today": days_until == 0,
                "emoji": WASTE_TYPE_EMOJIS.get(self._waste_type, "📦"),
            }
        return {}
