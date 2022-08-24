"""Adds config flow for HKO."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_CLIMATE_STATION_ID, CONF_FORECAST_STATION_ID, DOMAIN


class HKOConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            climate_station_id = user_input[CONF_CLIMATE_STATION_ID]
            forecast_station_id = user_input[CONF_FORECAST_STATION_ID]
            await self.async_set_unique_id(f"${climate_station_id}-${forecast_station_id}" , raise_on_progress=False)
            return self.async_create_entry(
                title=user_input[CONF_NAME], data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CLIMATE_STATION_ID, default="HKO"
                    ): str,
                    vol.Required(
                        CONF_FORECAST_STATION_ID, default="HKO"
                    ): str,
                    vol.Optional(
                        CONF_NAME, default=self.hass.config.location_name
                    ): str,
                }
            ),
            errors=errors,
        )
