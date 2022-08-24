"""Sensors for HKO."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, cast
from collections.abc import Mapping

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    TEMP_CELSIUS,
    PRESSURE_HPA,
)
from homeassistant.core import HomeAssistant, callback
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
        native_unit_of_measurement=TEMP_CELSIUS,
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
)

WARNING_SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="WTCPRE8",
        name="Pre-no.8 Special Announcement",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="WTCSGNL",
        name="Tropical Cyclone Warning Signal",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="tclevel",
        name="Tropical Cyclone Warning Level",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add HKO entities from a config_entry."""
    coordinator: HKODataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = [
        HKOWeatherSensor(coordinator, description) for description in SENSOR_TYPES
    ]
    sensors.extend(
        HKOWarningSensor(coordinator, description) for description in WARNING_SENSOR_TYPES
    )
    async_add_entities(sensors)


class HKOWeatherSensor(CoordinatorEntity[HKODataUpdateCoordinator], SensorEntity):
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    entity_description: SensorEntityDescription

    def __init__(self, coordinator: HKODataUpdateCoordinator, description: SensorEntityDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._sensor_data = coordinator.data[ATTR_AWS][description.key]
        self._attr_unique_id = f"${coordinator.climate_station_id}-${coordinator.forecast_station_id}-${description.key}"

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
        self._sensor_data = self._parse_warning(description, coordinator.data[ATTR_WARNINGS])
        self._attrs: dict[str, Any] = {}
        self._attr_unique_id = f"${coordinator.climate_station_id}-${coordinator.forecast_station_id}-${description.key}"

    @staticmethod
    def _parse_warning(description: SensorEntityDescription, data: dict[str, Any]) -> Any:
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
        self._sensor_data = self._parse_warning(self.entity_description, self.coordinator.data[ATTR_WARNINGS])
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self._sensor_data is not None and isinstance(self._sensor_data, Mapping):
            if "contents" in self._sensor_data:
                self._attrs["contents"] = '\n\n'.join(self._sensor_data['contents'])
        return self._attrs
