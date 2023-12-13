"""Sensors for HKO."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, cast
from collections.abc import Mapping

from homeassistant.components.sensor import (
    ENTITY_ID_FORMAT,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.components.binary_sensor import (
    ENTITY_ID_FORMAT as BINARY_SENSOR_ENTITY_ID_FORMAT,
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    TEMP_CELSIUS,
    PRESSURE_HPA,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .hko_data import HKODataUpdateCoordinator
from .const import (
    ATTR_AWS,
    ATTR_WARNINGS,
    ATTRIBUTION,
    DOMAIN,
)

PARALLEL_UPDATES = 1


SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="TEMP",
        device_class=SensorDeviceClass.TEMPERATURE,
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="RH",
        device_class=SensorDeviceClass.HUMIDITY,
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="PRESSURE",
        device_class=SensorDeviceClass.PRESSURE,
        name="Pressure",
        native_unit_of_measurement=PRESSURE_HPA,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="WINDSPEED",
        device_class=SensorDeviceClass.WIND_SPEED,
        name="Wind Speed",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="GUST",
        device_class=SensorDeviceClass.WIND_SPEED,
        name="Wind Gust",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="WINDDIRECTION",
        name="Wind Direction",
        icon="mdi:compass-outline",
        entity_registry_enabled_default=False,
    ),
)

WARNING_SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="WTCSGNL",
        name="Tropical Cyclone Warning Signal",
        icon="mdi:weather-hurricane",
    ),
    SensorEntityDescription(
        key="tclevel",
        name="Tropical Cyclone Warning Level",
        icon="mdi:weather-hurricane",
    ),
    SensorEntityDescription(
        key="WRAIN",
        name="Rainstorm Warning Signal",
        icon="mdi:weather-pouring",
    ),
)

BINARY_WARNING_SENSOR_TYPES: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="WFIRE",
        name="Fire Danger Warning",
        icon="mdi:fire-alert",
    ),
    BinarySensorEntityDescription(
        key="WFROST",
        name="Frost Warning",
        icon="mdi:snowflake-alert",
    ),
    BinarySensorEntityDescription(
        key="WHOT",
        name="Hot Weather Warning",
        icon="mdi:weather-sunny-alert",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    BinarySensorEntityDescription(
        key="WCOLD",
        name="Cold Weather Warning",
        icon="mdi:snowflake-thermometer",
        device_class=BinarySensorDeviceClass.COLD,
    ),
    BinarySensorEntityDescription(
        key="WMSGNL",
        name="Strong Monsoon Signal",
        icon="mdi:weather-windy",
    ),
    BinarySensorEntityDescription(
        key="WTCPRE8",
        name="Pre-no.8 Special Announcement",
        icon="mdi:numeric-8-box",
    ),
    BinarySensorEntityDescription(
        key="WFNTSA",
        name="Special Announcement on Flooding in the northern New Territories",
        icon="mdi:home-flood",
    ),
    BinarySensorEntityDescription(
        key="WL",
        name="Landslip Warning",
        icon="mdi:landslide",
    ),
    BinarySensorEntityDescription(
        key="WTMW",
        name="Tsunami Warning",
        icon="mdi:tsunami",
    ),
    BinarySensorEntityDescription(
        key="WTS",
        name="Thunderstorm Warning",
        icon="mdi:weather-lightning-rainy",
        device_class=BinarySensorDeviceClass.MOISTURE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add HKO entities from a config_entry."""
    coordinator: HKODataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = [HKOWeatherSensor(coordinator, description) for description in SENSOR_TYPES]
    sensors.extend(HKOWarningSensor(coordinator, description) for description in WARNING_SENSOR_TYPES)
    sensors.extend(HKOBinaryWarningSensor(coordinator, description) for description in BINARY_WARNING_SENSOR_TYPES)
    async_add_entities(sensors)


class HKOWeatherSensor(CoordinatorEntity[HKODataUpdateCoordinator], SensorEntity):
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    entity_description: SensorEntityDescription

    def __init__(self, coordinator: HKODataUpdateCoordinator, description: SensorEntityDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._sensor_data = coordinator.data[ATTR_AWS][description.key]
        self._attr_name = description.name
        self._attr_unique_id = f"{coordinator.climate_station_id}_{description.key}"
        self.entity_id = ENTITY_ID_FORMAT.format(f"{self._attr_unique_id}")

    @property
    def native_value(self) -> Any:
        return float(self._sensor_data)

    @callback
    def _handle_coordinator_update(self) -> None:
        self._sensor_data = self.coordinator.data[ATTR_AWS][self.entity_description.key]
        self.async_write_ha_state()


class HKOWarningSensor(CoordinatorEntity[HKODataUpdateCoordinator], SensorEntity):
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    entity_description: SensorEntityDescription

    def __init__(self, coordinator: HKODataUpdateCoordinator, description: SensorEntityDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._sensor_data = _parse_warning(description, coordinator.data[ATTR_WARNINGS])
        self._attrs: dict[str, Any] = {}
        self._attr_name = description.name
        self._attr_unique_id = description.key
        self.entity_id = ENTITY_ID_FORMAT.format(f"hko_{description.key}")

    @property
    def native_value(self) -> Any:
        if self._sensor_data is None:
            return None
        if isinstance(self._sensor_data, Mapping):
            if "subtype" in self._sensor_data:
                return self._sensor_data["subtype"]
            return "Active"
        return self._sensor_data

    @callback
    def _handle_coordinator_update(self) -> None:
        self._sensor_data = _parse_warning(self.entity_description, self.coordinator.data[ATTR_WARNINGS])
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self._sensor_data is not None and isinstance(self._sensor_data, Mapping):
            if "contents" in self._sensor_data:
                self._attrs["contents"] = '\n\n'.join(self._sensor_data['contents'])
        return self._attrs


class HKOBinaryWarningSensor(CoordinatorEntity[HKODataUpdateCoordinator], BinarySensorEntity):
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    entity_description: BinarySensorEntityDescription

    def __init__(self, coordinator: HKODataUpdateCoordinator, description: BinarySensorEntityDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._sensor_data = _parse_warning(description, coordinator.data[ATTR_WARNINGS])
        self._attrs: dict[str, Any] = {}
        self._attr_name = description.name
        self._attr_unique_id = description.key
        self.entity_id = BINARY_SENSOR_ENTITY_ID_FORMAT.format(f"hko_{description.key}")

    @property
    def is_on(self) -> bool:
        return self._sensor_data is not None

    @callback
    def _handle_coordinator_update(self) -> None:
        self._sensor_data = _parse_warning(self.entity_description, self.coordinator.data[ATTR_WARNINGS])
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self._sensor_data is not None and isinstance(self._sensor_data, Mapping):
            if "contents" in self._sensor_data:
                self._attrs["contents"] = '\n\n'.join(self._sensor_data['contents'])
        return self._attrs


def _parse_warning(description: EntityDescription, data: dict[str, Any]) -> Any:
    if description.key == "tclevel":
        if "WTCSGNL" in data:
            subtype = data["WTCSGNL"]["subtype"]
            if subtype.startswith("TC"):
                return int(re.compile("TC(\d+)").match(subtype).group(1))
        return None
    try:
        return data[description.key]
    except KeyError:
        return None
