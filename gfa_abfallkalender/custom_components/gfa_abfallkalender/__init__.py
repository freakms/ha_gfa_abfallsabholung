"""GFA Abfallkalender Integration for Home Assistant."""
import logging
from datetime import datetime, time, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.event import async_track_time_change

from .const import (
    DOMAIN,
    CONF_ICS_URL,
    CONF_REMINDER_TIME,
    CONF_REMINDER_DAYS_BEFORE,
    CONF_ALEXA_ENTITY,
    CONF_ENABLED_WASTE_TYPES,
    SERVICE_ANNOUNCE,
    SERVICE_REFRESH,
    WASTE_TYPE_NAMES,
    PLATFORMS,
)
from .coordinator import GFADataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS_LIST = [Platform.SENSOR, Platform.CALENDAR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GFA Abfallkalender from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create coordinator
    coordinator = GFADataCoordinator(
        hass,
        entry.data[CONF_ICS_URL],
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "config": entry.data,
        "unsub_reminder": None,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_LIST)

    # Set up reminder
    await _setup_reminder(hass, entry)

    # Register services
    await _register_services(hass)

    return True


async def _setup_reminder(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up the daily reminder."""
    reminder_time_str = entry.data.get(CONF_REMINDER_TIME, "19:00")
    hour, minute = map(int, reminder_time_str.split(":"))

    async def _reminder_callback(now: datetime) -> None:
        """Handle reminder callback."""
        await _announce_tomorrow_pickups(hass, entry)

    # Cancel existing reminder if any
    if hass.data[DOMAIN][entry.entry_id].get("unsub_reminder"):
        hass.data[DOMAIN][entry.entry_id]["unsub_reminder"]()

    # Set up new reminder
    unsub = async_track_time_change(
        hass, _reminder_callback, hour=hour, minute=minute, second=0
    )
    hass.data[DOMAIN][entry.entry_id]["unsub_reminder"] = unsub
    _LOGGER.info(f"Reminder set for {hour:02d}:{minute:02d}")


async def _announce_tomorrow_pickups(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Announce tomorrow's waste pickups via Alexa."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    config = entry.data

    alexa_entity = config.get(CONF_ALEXA_ENTITY)
    if not alexa_entity:
        _LOGGER.warning("No Alexa entity configured")
        return

    enabled_types = config.get(CONF_ENABLED_WASTE_TYPES, [])
    days_before = config.get(CONF_REMINDER_DAYS_BEFORE, 1)

    # Calculate target date
    target_date = datetime.now().date() + timedelta(days=days_before)

    # Get pickups for target date
    pickups = coordinator.get_pickups_for_date(target_date)

    if not pickups:
        _LOGGER.debug(f"No pickups scheduled for {target_date}")
        return

    # Filter by enabled waste types
    filtered_pickups = []
    for pickup in pickups:
        waste_type = pickup.get("waste_type")
        if not enabled_types or waste_type in enabled_types:
            filtered_pickups.append(pickup)

    if not filtered_pickups:
        _LOGGER.debug("No enabled waste types scheduled")
        return

    # Build announcement message
    waste_names = []
    for pickup in filtered_pickups:
        waste_type = pickup.get("waste_type")
        friendly_name = WASTE_TYPE_NAMES.get(waste_type, pickup.get("summary", waste_type))
        waste_names.append(friendly_name)

    if days_before == 1:
        day_text = "morgen"
    elif days_before == 0:
        day_text = "heute"
    else:
        day_text = f"in {days_before} Tagen"

    waste_list = ", ".join(waste_names[:-1]) + " und " + waste_names[-1] if len(waste_names) > 1 else waste_names[0]
    
    message = f"Abholtermin der GFA {day_text}. Abgeholt wird {waste_list}. Alexa Stop."

    _LOGGER.info(f"Announcing: {message}")

    # Call Alexa Media Player notify service
    await hass.services.async_call(
        "notify",
        alexa_entity.replace("media_player.", "alexa_media_"),
        {"message": message, "data": {"type": "announce"}},
    )


async def _register_services(hass: HomeAssistant) -> None:
    """Register integration services."""

    async def handle_announce(call: ServiceCall) -> None:
        """Handle manual announce service call."""
        for entry_id, data in hass.data[DOMAIN].items():
            if isinstance(data, dict) and "coordinator" in data:
                entry = hass.config_entries.async_get_entry(entry_id)
                if entry:
                    await _announce_tomorrow_pickups(hass, entry)

    async def handle_refresh(call: ServiceCall) -> None:
        """Handle refresh service call."""
        for entry_id, data in hass.data[DOMAIN].items():
            if isinstance(data, dict) and "coordinator" in data:
                await data["coordinator"].async_refresh()

    if not hass.services.has_service(DOMAIN, SERVICE_ANNOUNCE):
        hass.services.async_register(DOMAIN, SERVICE_ANNOUNCE, handle_announce)

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        hass.services.async_register(DOMAIN, SERVICE_REFRESH, handle_refresh)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Cancel reminder
    if unsub := hass.data[DOMAIN][entry.entry_id].get("unsub_reminder"):
        unsub()

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS_LIST)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
