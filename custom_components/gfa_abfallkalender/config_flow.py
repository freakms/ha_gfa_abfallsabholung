"""Config flow for GFA Abfallkalender with address lookup."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.entity_registry as er

from .api import GFALueneburgAPI
from .const import (
    DOMAIN,
    CONF_CITY,
    CONF_STREET,
    CONF_HOUSE_NUMBER,
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
        self._api = GFALueneburgAPI()
        self._city: str | None = None
        self._street: str | None = None
        self._house_number: str | None = None
        self._waste_types: list[str] = []
        self._cities: list[str] = []
        self._streets: list[str] = []
        self._house_numbers: list[str] = []
        self._reminder_config: dict[str, Any] = {}
        self._alexa_config: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - city selection."""
        errors = {}

        if user_input is not None:
            self._city = user_input[CONF_CITY]
            return await self.async_step_street()

        # Fetch cities from GFA
        try:
            self._cities = await self._api.get_cities()
        except Exception as err:
            _LOGGER.error(f"Error fetching cities: {err}")
            errors["base"] = "cannot_connect"

        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({vol.Required(CONF_CITY): str}),
                errors=errors,
            )

        # Create city selector options
        city_options = [
            selector.SelectOptionDict(value=city, label=city)
            for city in self._cities
        ]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CITY): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=city_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_street(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle street selection."""
        errors = {}

        if user_input is not None:
            self._street = user_input[CONF_STREET]
            return await self.async_step_house_number()

        # Fetch streets for selected city
        try:
            self._streets = await self._api.get_streets(self._city)
        except Exception as err:
            _LOGGER.error(f"Error fetching streets: {err}")
            errors["base"] = "cannot_connect"
            return self.async_show_form(
                step_id="street",
                data_schema=vol.Schema({vol.Required(CONF_STREET): str}),
                errors=errors,
            )

        # Create street selector options
        street_options = [
            selector.SelectOptionDict(value=street, label=street)
            for street in self._streets
        ]

        return self.async_show_form(
            step_id="street",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STREET): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=street_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
            description_placeholders={"city": self._city},
        )

    async def async_step_house_number(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle house number selection."""
        errors = {}

        if user_input is not None:
            self._house_number = user_input[CONF_HOUSE_NUMBER]
            
            # Try to fetch ICS to detect waste types
            try:
                ics_content = await self._api.get_ics_calendar(
                    self._city, self._street, self._house_number
                )
                self._waste_types = self._detect_waste_types(ics_content)
            except Exception as err:
                _LOGGER.error(f"Error fetching ICS: {err}")
                # Continue anyway, we can detect types later
                self._waste_types = list(WASTE_TYPE_NAMES.keys())
            
            return await self.async_step_reminder()

        # Fetch house numbers for selected street
        try:
            self._house_numbers = await self._api.get_house_numbers(
                self._city, self._street
            )
        except Exception as err:
            _LOGGER.error(f"Error fetching house numbers: {err}")
            errors["base"] = "cannot_connect"
            return self.async_show_form(
                step_id="house_number",
                data_schema=vol.Schema({vol.Required(CONF_HOUSE_NUMBER): str}),
                errors=errors,
            )

        # Create house number selector options
        house_options = [
            selector.SelectOptionDict(value=hn, label=hn)
            for hn in self._house_numbers
        ]

        return self.async_show_form(
            step_id="house_number",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOUSE_NUMBER): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=house_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
            description_placeholders={"city": self._city, "street": self._street},
        )

    def _detect_waste_types(self, ics_content: str) -> list[str]:
        """Detect waste types from ICS content."""
        from .const import WASTE_TYPE_MAPPINGS
        
        waste_types = set()
        ics_lower = ics_content.lower()
        
        for waste_type, keywords in WASTE_TYPE_MAPPINGS.items():
            for keyword in keywords:
                if keyword in ics_lower:
                    waste_types.add(waste_type)
                    break
        
        if not waste_types:
            # Return all types if none detected
            return list(WASTE_TYPE_NAMES.keys())
        
        return list(waste_types)

    async def async_step_reminder(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the reminder configuration step."""
        errors = {}

        if user_input is not None:
            self._reminder_config = user_input
            return await self.async_step_alexa()

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
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle Alexa device selection."""
        errors = {}

        if user_input is not None:
            self._alexa_config = user_input
            return await self.async_step_waste_types()

        # Get available Alexa Media Player entities
        entity_registry = er.async_get(self.hass)
        alexa_entities = [
            entry.entity_id
            for entry in entity_registry.entities.values()
            if entry.entity_id.startswith("media_player.")
            and ("alexa" in entry.entity_id.lower() or entry.platform == "alexa_media")
        ]

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
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle waste type selection."""
        errors = {}

        if user_input is not None:
            # Close the API session
            await self._api.close()
            
            # Create the config entry
            return self.async_create_entry(
                title=f"GFA {self._city} - {self._street} {self._house_number}",
                data={
                    CONF_CITY: self._city,
                    CONF_STREET: self._street,
                    CONF_HOUSE_NUMBER: self._house_number,
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
