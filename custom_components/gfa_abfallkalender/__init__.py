"""GFA Abfallkalender Integration for Home Assistant."""
import logging
from datetime import datetime, time, timedelta
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.event import async_track_time_change

from .const import (
    DOMAIN,
    CONF_CITY,
    CONF_STREET,
    CONF_HOUSE_NUMBER,
    CONF_REMINDER_TIME,
    CONF_REMINDER_DAYS_BEFORE,
    CONF_ALEXA_ENTITY,
    CONF_ENABLED_WASTE_TYPES,
    SERVICE_ANNOUNCE,
    SERVICE_REFRESH,
    WASTE_TYPE_NAMES,
)
from .coordinator import GFADataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS_LIST = [Platform.SENSOR, Platform.CALENDAR]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register static path for the custom Lovelace grid card."""
    js_file = Path(__file__).parent / "www" / "gfa-abfall-grid-card.js"
    if js_file.is_file():
        hass.http.register_static_path(
            f"/{DOMAIN}/gfa-abfall-grid-card.js",
            str(js_file),
            cache_headers=False,
        )
        _LOGGER.info("GFA Grid Card verfügbar unter /%s/gfa-abfall-grid-card.js", DOMAIN)
    else:
        _LOGGER.error("GFA Grid Card JS nicht gefunden: %s", js_file)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GFA Abfallkalender from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create coordinator with config data
    coordinator = GFADataCoordinator(hass, entry.data)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "config": entry.data,
        "unsub_reminder": None,
        "unsub_options_listener": None,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_LIST)

    # Set up reminder
    await _setup_reminder(hass, entry)

    # Register services
    await _register_services(hass)

    # Listen for options changes and re-apply reminder immediately
    async def _options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Re-apply reminder when options are changed."""
        _LOGGER.debug("Options updated, re-applying reminder")
        await _setup_reminder(hass, entry)

    unsub_listener = entry.add_update_listener(_options_updated)
    hass.data[DOMAIN][entry.entry_id]["unsub_options_listener"] = unsub_listener

    return True


async def _setup_reminder(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up the daily reminder, reading options before data."""
    # Options override data so live changes take effect immediately
    config = {**entry.data, **entry.options}
    reminder_time_str = config.get(CONF_REMINDER_TIME, "19:00")

    # Handle all three possible formats:
    #   dict  {"hour": 19, "minute": 0}      (older HA versions)
    #   str   "HH:MM"                         (manually set)
    #   str   "HH:MM:SS"                      (TimeSelector in current HA)
    if isinstance(reminder_time_str, dict):
        hour = int(reminder_time_str.get("hour", 19))
        minute = int(reminder_time_str.get("minute", 0))
    else:
        parts = str(reminder_time_str).split(":")
        hour = int(parts[0])
        minute = int(parts[1])

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
    # Options take priority over initial data (same as _setup_reminder)
    config = {**entry.data, **entry.options}

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

    # Filter by enabled waste types and deduplicate by waste_type
    seen_types: set[str] = set()
    filtered_pickups = []
    for pickup in pickups:
        waste_type = pickup.get("waste_type")
        if waste_type in seen_types:
            continue
        if not enabled_types or waste_type in enabled_types:
            seen_types.add(waste_type)
            filtered_pickups.append(pickup)

    if not filtered_pickups:
        _LOGGER.debug("No enabled waste types scheduled")
        return

    # Build announcement message
    waste_names = []
    for pickup in filtered_pickups:
        waste_type = pickup.get("waste_type")
        friendly_name = WASTE_TYPE_NAMES.get(
            waste_type, pickup.get("summary", waste_type)
        )
        waste_names.append(friendly_name)

    if days_before == 1:
        day_text = "morgen"
    elif days_before == 0:
        day_text = "heute"
    else:
        day_text = f"in {days_before} Tagen"

    if len(waste_names) > 1:
        waste_list = ", ".join(waste_names[:-1]) + " und " + waste_names[-1]
    else:
        waste_list = waste_names[0]

    message = f"Abholtermin der GFA {day_text}. Abgeholt wird {waste_list}."

    _LOGGER.info(f"Announcing: {message}")

    # Try Alexa Media Player notify service first
    # The notify service name is derived from the entity_id:
    # media_player.mein_echo  →  notify.alexa_media_mein_echo
    entity_slug = alexa_entity.replace("media_player.", "")
    alexa_notify_service = f"alexa_media_{entity_slug}"

    try:
        await hass.services.async_call(
            "notify",
            alexa_notify_service,
            {"message": message, "data": {"type": "announce"}},
        )
        _LOGGER.debug(f"Announcement sent via notify.{alexa_notify_service}")
        return
    except Exception as e:
        _LOGGER.warning(f"notify.{alexa_notify_service} failed: {e}")

    # Fallback: media_player.play_media with Alexa TTS type
    try:
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": alexa_entity,
                "media_content_id": message,
                "media_content_type": "sound",
                "extra": {"announcement": True},
            },
        )
        _LOGGER.debug("Announcement sent via media_player.play_media")
        return
    except Exception as e:
        _LOGGER.warning(f"media_player.play_media failed: {e}")

    # Last resort: tts.speak
    try:
        await hass.services.async_call(
            "tts",
            "speak",
            {
                "entity_id": alexa_entity,
                "message": message,
            },
        )
        _LOGGER.debug("Announcement sent via tts.speak")
    except Exception as e:
        _LOGGER.error(f"All announcement methods failed: {e}")


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

    # Cancel options listener
    if unsub := hass.data[DOMAIN][entry.entry_id].get("unsub_options_listener"):
        unsub()

    # Close API session
    coordinator = hass.data[DOMAIN][entry.entry_id].get("coordinator")
    if coordinator:
        await coordinator.async_close()

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS_LIST)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
