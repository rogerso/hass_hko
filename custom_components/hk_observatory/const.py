"""Constants for the Hong Kong Observatory integration."""

from typing import Final

DOMAIN:Final = "hk_observatory"

ATTRIBUTION: Final = "Data provided by Hong Kong Observatory"
CONF_CLIMATE_STATION_ID: Final = "climate_station_id"
CONF_FORECAST_STATION_ID: Final = "forecast_station_id"

ATTR_AWS_LAST_UPDATED = "_aws_last_updated"
ATTR_FORECAST_LAST_UPDATED = "_forecast_last_updated"

ATTR_AWS = "_aws"
ATTR_FORECAST = "_forecast"
ATTR_DAILY_FORECAST = "_daily_forecast"
ATTR_OTHER = "_other"
ATTR_WARNINGS = "_warn"

# https://www.hko.gov.hk/textonly/v2/explain/wxicon_e.htm
MAP_CONDITION = {
    50: "sunny",
    51: "partlycloudy",
    52: "partlycloudy",
    53: "rainy",
    54: "rainy",
    60: "cloudy",
    61: "cloudy",
    62: "rainy",
    63: "rainy",
    64: "pouring",
    65: "lightning-rainy",
    70: "clear-night",
    701: "cloudy",
    702: "partlycloudy",
    71: "clear-night",
    711: "cloudy",
    712: "partlycloudy",
    72: "clear-night",
    721: "cloudy",
    722: "partlycloudy",
    73: "clear-night",
    731: "cloudy",
    732: "partlycloudy",
    74: "clear-night",
    741: "cloudy",
    742: "partlycloudy",
    75: "clear-night",
    751: "cloudy",
    752: "partlycloudy",
    76: "cloudy",
    77: "partlycloudy",
    80: "windy",
    83: "fog",
    84: "fog",
    85: "fog",
}


