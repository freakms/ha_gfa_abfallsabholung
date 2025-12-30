"""Config flow for GFA Abfallkalender."""
import logging
from typing import Any

import aiohttp
import voluptuous as vol
from icalendar import Calendar

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.entity_registry as er

from .const import (
    DOMAIN,
    CONF_ICS_URL,
    CONF_REMINDER_TIME,
    CONF_REMINDER_DAYS_BEFORE,
    CONF_ALEXA_ENTITY,
    CONF_ENABLED_WASTE_TYPES,
    DEFAULT_REMINDER_TIME,
    DEFAULT_REMINDER_DAYS_BEFORE,
    WASTE_TYPE_NAMES,
)

_LOGGER = logging.getLogger(__name__)


class GFAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GFA Abfallkalender."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._ics_url: str | None = None
        self._waste_types: list[str] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - ICS URL input."""
        errors = {}

        if user_input is not None:
            ics_url = user_input[CONF_ICS_URL]
            
            # Validate ICS URL
            valid, waste_types, error = await self._validate_ics_url(ics_url)
            
            if valid:
                self._ics_url = ics_url
                self._waste_types = waste_types
                return await self.async_step_reminder()
            else:
                errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ICS_URL): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "example_url": "https://gfa-lueneburg.de/kalender.ics"
            },
        )

    async def async_step_reminder(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the reminder configuration step."""
        errors = {}

        if user_input is not None:
            return await self.async_step_alexa(user_input)

        return self.async_show_form(
            step_id="reminder",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_REMINDER_DAYS_BEFORE, default=DEFAULT_REMINDER_DAYS_BEFORE
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=7,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="Tage vorher",
                        )
                    ),
                    vol.Required(
                        CONF_REMINDER_TIME, default=DEFAULT_REMINDER_TIME
                    ): selector.TimeSelector(),
                }
            ),
            errors=errors,
        )

    async def async_step_alexa(
        self, reminder_input: dict[str, Any], user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle Alexa device selection."""
        errors = {}

        # Store reminder input for later
        self._reminder_config = reminder_input

        if user_input is not None:
            return await self.async_step_waste_types(user_input)

        # Get available Alexa Media Player entities
        entity_registry = er.async_get(self.hass)
        alexa_entities = [
            entry.entity_id
            for entry in entity_registry.entities.values()
            if entry.entity_id.startswith("media_player.")
            and "alexa" in entry.entity_id.lower()
        ]

        # Also check for entities without "alexa" in the ID but from alexa_media domain
        for entry in entity_registry.entities.values():
            if (
                entry.entity_id.startswith("media_player.")
                and entry.platform == "alexa_media"
                and entry.entity_id not in alexa_entities
            ):
                alexa_entities.append(entry.entity_id)

        if not alexa_entities:
            # Allow manual input if no Alexa devices found
            alexa_entities = ["media_player.echo_dot", "media_player.echo_show"]

        return self.async_show_form(
            step_id="alexa",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ALEXA_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="media_player",
                            multiple=False,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_waste_types(
        self, alexa_input: dict[str, Any], user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle waste type selection."""
        errors = {}

        # Store alexa input
        self._alexa_config = alexa_input

        if user_input is not None:
            # Create the config entry
            return self.async_create_entry(
                title="GFA Abfallkalender",
                data={
                    CONF_ICS_URL: self._ics_url,
                    CONF_REMINDER_DAYS_BEFORE: self._reminder_config.get(
                        CONF_REMINDER_DAYS_BEFORE, DEFAULT_REMINDER_DAYS_BEFORE
                    ),
                    CONF_REMINDER_TIME: self._reminder_config.get(
                        CONF_REMINDER_TIME, DEFAULT_REMINDER_TIME
                    ),
                    CONF_ALEXA_ENTITY: self._alexa_config.get(CONF_ALEXA_ENTITY),
                    CONF_ENABLED_WASTE_TYPES: user_input.get(
                        CONF_ENABLED_WASTE_TYPES, self._waste_types
                    ),
                },
            )

        # Create options for waste types
        waste_type_options = [
            selector.SelectOptionDict(
                value=wt,
                label=WASTE_TYPE_NAMES.get(wt, wt),
            )
            for wt in self._waste_types
        ]

        return self.async_show_form(
            step_id="waste_types",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ENABLED_WASTE_TYPES, default=self._waste_types
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=waste_type_options,
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def _validate_ics_url(self, url: str) -> tuple[bool, list[str], str | None]:
        """Validate the ICS URL and extract waste types."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        return False, [], "cannot_connect"
                    
                    ics_content = await response.text()

            # Try to parse the calendar
            calendar = Calendar.from_ical(ics_content)
            
            # Extract waste types from events
            from .const import WASTE_TYPE_MAPPINGS
            
            waste_types = set()
            for component in calendar.walk():
                if component.name == "VEVENT":
                    summary = str(component.get("SUMMARY", "")).lower()
                    for waste_type, keywords in WASTE_TYPE_MAPPINGS.items():
                        for keyword in keywords:
                            if keyword in summary:
                                waste_types.add(waste_type)
                                break

            if not waste_types:
                # Add "unknown" if no recognized types found
                waste_types.add("unknown")

            return True, list(waste_types), None

        except aiohttp.ClientError:
            return False, [], "cannot_connect"
        except Exception as err:
            _LOGGER.error(f"Error validating ICS: {err}")
            return False, [], "invalid_ics"

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Get the options flow for this handler."""
        return GFAOptionsFlow(config_entry)


class GFAOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for GFA Abfallkalender."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_config = self.config_entry.data

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_REMINDER_DAYS_BEFORE,
                        default=current_config.get(
                            CONF_REMINDER_DAYS_BEFORE, DEFAULT_REMINDER_DAYS_BEFORE
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=7,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="Tage vorher",
                        )
                    ),
                    vol.Required(
                        CONF_REMINDER_TIME,
                        default=current_config.get(
                            CONF_REMINDER_TIME, DEFAULT_REMINDER_TIME
                        ),
                    ): selector.TimeSelector(),
                    vol.Required(
                        CONF_ALEXA_ENTITY,
                        default=current_config.get(CONF_ALEXA_ENTITY),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="media_player",
                            multiple=False,
                        )
                    ),
                }
            ),
        )
