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
            }
        return {}
