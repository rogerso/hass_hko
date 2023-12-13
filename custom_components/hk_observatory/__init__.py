"""The Hong Kong Observatory integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo

from .const import CONF_CLIMATE_STATION_ID, CONF_FORECAST_STATION_ID, DOMAIN
from .hko_data import HKODataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.WEATHER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hong Kong Observatory from a config entry."""

    assert entry.unique_id is not None
    site_name = entry.data[CONF_NAME]

    # TODO - try to get the closest station to the given lat/long
    climate_station_id = entry.data[CONF_CLIMATE_STATION_ID]
    forecast_station_id = entry.data[CONF_FORECAST_STATION_ID]

    websession = async_get_clientsession(hass)
    coordinator = HKODataUpdateCoordinator(hass, websession, climate_station_id, forecast_station_id, site_name)
    await coordinator.async_config_entry_first_refresh()

    hko_hass_data = hass.data.setdefault(DOMAIN, {})
    hko_hass_data[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


def get_device_info(name: str, climate_station_id: str, forecast_station_id: str) -> DeviceInfo:
    """Return device information about this entity."""
    return DeviceInfo(
        entry_type=device_registry.DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, climate_station_id, forecast_station_id)},
        manufacturer="Hong Kong Observatory",
        name=f"HKO",
    )
