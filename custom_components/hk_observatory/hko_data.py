from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

import csv

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientConnectorError
from async_timeout import timeout

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
import homeassistant.util.dt as dt_util

from .const import (
  ATTR_AWS,
  ATTR_FORECAST,
  ATTR_DAILY_FORECAST,
  ATTR_OTHER,
  ATTR_WARNINGS,
  DOMAIN,
  ATTR_AWS_LAST_UPDATED,
  ATTR_FORECAST_LAST_UPDATED,
)

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)


class HKODataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching HKO data."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: ClientSession,
        climate_station_id: str,
        forecast_station_id: str,
        name: str,
    ) -> None:
        """Initialize."""
        self.name = name
        self.session = session
        self.climate_station_id = climate_station_id
        self.forecast_station_id = forecast_station_id

        update_interval = MIN_TIME_BETWEEN_UPDATES
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_get_station_data(self) -> dict[str, Any]:
        """Get automatic weather station (AWS) observations."""
        resp = await self.session.get("https://www.hko.gov.hk/wxinfo/awsgis/latestReadings_AWS1_v2.txt")
        rawdata = await resp.text()
        firstline, datalines = rawdata.split('\n', 1)
        datareader = csv.DictReader(datalines.split('\n'))
        rawdata = dict([(x['STN'], x) for x in datareader])
        data = rawdata[self.climate_station_id]
        data[ATTR_AWS_LAST_UPDATED] = dt_util.as_utc(
            datetime.strptime(
                str(firstline) + " +0800", "Latest readings recorded at %H:%M Hong Kong Time %d %B %Y %z"
            )
        )
        return data

    async def _async_get_forecast_data(self) -> list[dict[str, Any]]:
        """Get forecast data."""
        url = f"https://maps.weather.gov.hk/ocf/dat/{self.forecast_station_id}.xml"
        resp = await self.session.get(url)
        rawdata = await resp.json(content_type=None)
        data = {
            "hourly": rawdata["HourlyWeatherForecast"],
            "daily": rawdata["DailyForecast"],
            "last_modified": dt_util.as_utc(
                datetime.strptime(
                    str(rawdata["LastModified"]) + " +0800", "%Y%m%d%H%M%S %z"
                )
            ),
        }
        return data

    async def _async_get_other_data(self) -> dict[str, Any]:
        resp = await self.session.get("https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=en")
        data = await resp.json()
        return data

    async def _async_get_warnings(self) -> dict[str, Any]:
        """Get warnings."""
        # We use warningInfo instead of warnsum because warnsum does not have pre-T8 signal
        resp = await self.session.get("https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=warningInfo&lang=en")
        rawdata = await resp.json()
        try:
            return dict([(i['warningStatementCode'], i) for i in rawdata['details']])
        except KeyError:
            return {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data."""
        try:
            async with timeout(10):
                aws = await self._async_get_station_data()
                forecast = await self._async_get_forecast_data()
                other = await self._async_get_other_data()
                warnings = await self._async_get_warnings()
        except ClientConnectorError as error:
            raise UpdateFailed(error) from error
        return {
            ATTR_AWS: aws,
            ATTR_FORECAST: forecast["hourly"],
            ATTR_DAILY_FORECAST: forecast["daily"],
            ATTR_FORECAST_LAST_UPDATED: forecast["last_modified"],
            ATTR_OTHER: other,
            ATTR_WARNINGS: warnings,
        }
