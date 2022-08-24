"""Support for Hong Kong Observatory weather service."""
import logging
from datetime import datetime
import typing

from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    ATTR_FORECAST_WIND_SPEED,
    Forecast,
    WeatherEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    LENGTH_KILOMETERS,
    LENGTH_MILLIMETERS,
    PRESSURE_HPA,
    SPEED_KILOMETERS_PER_HOUR,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .hko_data import HKODataUpdateCoordinator
from .const import (
    ATTR_AWS,
    ATTR_FORECAST,
    ATTR_OTHER,
    ATTRIBUTION,
    DOMAIN,
    MAP_CONDITION,
)

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add an HKO weather entity from a config_entry."""
    coordinator: HKODataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HKOWeatherEntity(coordinator)])


class HKOWeatherEntity(CoordinatorEntity[HKODataUpdateCoordinator], WeatherEntity):
    """Representation of a weather condition."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: HKODataUpdateCoordinator) -> None:
        """Initialise the platform with a data instance."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.climate_station_id}-{coordinator.forecast_station_id}"
        self._attr_attribution = ATTRIBUTION
        self._attr_native_precipitation_unit = LENGTH_MILLIMETERS
        self._attr_native_pressure_unit = PRESSURE_HPA
        self._attr_native_temperature_unit = TEMP_CELSIUS
        self._attr_native_visibility_unit = LENGTH_KILOMETERS
        self._attr_native_wind_speed_unit = SPEED_KILOMETERS_PER_HOUR

    @property
    def condition(self) -> typing.Union[str, None]:
        """Return the current condition."""
        try:
            icon = self.coordinator.data[ATTR_OTHER]["icon"][0]
            return MAP_CONDITION.get(int(icon))
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def native_temperature(self):
        try:
            return float(self.coordinator.data[ATTR_AWS]["TEMP"])
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def native_pressure(self):
        try:
            return float(self.coordinator.data[ATTR_AWS]["PRESSURE"])
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def humidity(self):
        try:
            return float(self.coordinator.data[ATTR_AWS]["RH"])
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def native_visibility(self):
        try:
            return float(self.coordinator.data[ATTR_AWS]["VISIBILITY"]) / 1000
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def native_wind_speed(self):
        try:
            return float(self.coordinator.data[ATTR_AWS]["WINDSPEED"])
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def wind_bearing(self):
        try:
            return int(self.coordinator.data[ATTR_AWS]["WINDDIRECTION"])
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def forecast(self):
        data = [
            {
                ATTR_FORECAST_TIME: datetime.strptime(entry["ForecastHour"] + " +0800", "%Y%m%d%H %z").isoformat(),
                ATTR_FORECAST_NATIVE_TEMP: float(entry["ForecastTemperature"]) if "ForecastTemperature" in entry else None,
                ATTR_FORECAST_NATIVE_TEMP_LOW: float(entry["ForecastMinimumTemperature"]) if "ForecastMinimumTemperature" in entry else None,
                ATTR_FORECAST_WIND_BEARING: int(entry["ForecastWindDirection"]) if "ForecastWindDirection" in entry else None,
                ATTR_FORECAST_WIND_SPEED: float(entry["ForecastWindSpeed"]) if "ForecastWindSpeed" in entry else None,
                ATTR_FORECAST_CONDITION: MAP_CONDITION.get(int(entry["ForecastWeather"])) if "ForecastWeather" in entry else None,
            }
            for entry in self.coordinator.data[ATTR_FORECAST]
        ]
        return data
