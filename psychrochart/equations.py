# -*- coding: utf-8 -*-
"""A library to make psychrometric charts and overlay information in them."""
from psychrolib import (
    GetHumRatioFromVapPres,
    GetMoistAirEnthalpy,
    GetMoistAirVolume,
    GetRelHumFromTWetBulb,
    GetSatVapPres,
    GetStandardAtmPressure,
    GetTDewPointFromVapPres,
    GetTDryBulbFromEnthalpyAndHumRatio,
    GetTWetBulbFromRelHum,
    GetUnitSystem,
    GetVapPresFromHumRatio,
    SetUnitSystem,
    SI,
)

from .psychrolib_extra import GetTDryBulbFromMoistAirVolume

# Set SI unit system by default
if GetUnitSystem() is None:
    SetUnitSystem(SI)


def _get_dry_temp_for_constant_wet_temp(
    dbt, wbt, p_atm,
):
    return 1000 * humidity_ratio(
        saturation_pressure_water_vapor(dbt)
        * relative_humidity_from_temps(dbt, wbt, p_atm_kpa=p_atm),
        p_atm_kpa=p_atm,
    )


def pressure_by_altitude(altitude_m: float) -> float:
    """Obtain the standard pressure for a certain sea level."""
    return GetStandardAtmPressure(altitude_m) / 1000.0


def water_vapor_pressure(w_kg_kga: float, p_atm_kpa: float) -> float:
    """Obtain the water vapor pressure from the humidity ratio (w_kg_kga)."""
    return GetVapPresFromHumRatio(w_kg_kga, p_atm_kpa * 1000.0) / 1000.0


def humidity_ratio(p_vapor_kpa: float, p_atm_kpa: float) -> float:
    """Obtain the humidity ratio from the water vapor pressure."""
    return GetHumRatioFromVapPres(p_vapor_kpa * 1000.0, p_atm_kpa * 1000.0)


def relative_humidity_from_temps(
    dry_bulb_temp_c: float, wet_bulb_temp_c: float, p_atm_kpa: float,
) -> float:
    """Obtain the relative humidity from the dry and wet bulb temperatures."""
    return GetRelHumFromTWetBulb(
        dry_bulb_temp_c, wet_bulb_temp_c, p_atm_kpa * 1000.0
    )


def specific_volume(
    dry_temp_c: float, p_vapor_kpa: float, p_atm_kpa: float,
) -> float:
    """Obtain the specific volume v of a moist air mixture."""
    w_kg_kga = GetHumRatioFromVapPres(p_vapor_kpa * 1000.0, p_atm_kpa * 1000.0)
    return GetMoistAirVolume(dry_temp_c, w_kg_kga, p_atm_kpa * 1000.0)


def dry_temperature_for_specific_volume_of_moist_air(
    w_kg_kga: float, specific_vol: float, p_atm_kpa: float,
) -> float:
    """Solve the dry bulb temp from humidity ratio and specific volume."""
    return GetTDryBulbFromMoistAirVolume(
        specific_vol, w_kg_kga, p_atm_kpa * 1000.0
    )


def saturation_pressure_water_vapor(dry_temp_c: float) -> float:
    """Saturation pressure of water vapor (kPa) from dry temperature."""
    return GetSatVapPres(dry_temp_c) / 1000.0


def enthalpy_moist_air(
    dry_temp_c: float, p_vapor_kpa: float, p_atm_kpa: float,
) -> float:
    """Moist air specific enthalpy."""
    w_kg_kga = GetHumRatioFromVapPres(p_vapor_kpa * 1000.0, p_atm_kpa * 1000.0)
    return GetMoistAirEnthalpy(dry_temp_c, w_kg_kga) / 1000.0


def dry_temperature_for_enthalpy_of_moist_air(
    enthalpy: float, w_kg_kga: float
) -> float:
    """Solve the dry bulb temp from humidity ratio and specific enthalpy."""
    return GetTDryBulbFromEnthalpyAndHumRatio(enthalpy * 1000.0, w_kg_kga)


def dew_point_temperature(dry_temp_c: float, p_w_kpa: float) -> float:
    """Dew point temperature."""
    return GetTDewPointFromVapPres(dry_temp_c, p_w_kpa * 1000.0)


def wet_bulb_temperature(
    dry_temp_c: float, relative_humid: float, p_atm_kpa: float,
) -> float:
    """Wet bulb temperature."""
    return GetTWetBulbFromRelHum(
        dry_temp_c, min(relative_humid, 1.0), p_atm_kpa * 1000.0
    )
