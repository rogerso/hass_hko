"""The hko component."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_CLIMATE_STATION_ID, CONF_FORECAST_STATION_ID, DOMAIN
from .hko_data import HKODataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.WEATHER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HKO as config entry."""
    name: str = entry.data[CONF_NAME]
    assert entry.unique_id is not None
    climate_station_id: str = entry.options.get(CONF_CLIMATE_STATION_ID, "HKO")
    forecast_station_id = entry.options.get(CONF_FORECAST_STATION_ID, "HKO")

    _LOGGER.debug("Using climate_station_id: %s, forecast_station_id: %s", climate_station_id, forecast_station_id)

    websession = async_get_clientsession(hass)

    coordinator = HKODataUpdateCoordinator(hass, websession, climate_station_id, forecast_station_id, name)
    await coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(update_listener))

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)
