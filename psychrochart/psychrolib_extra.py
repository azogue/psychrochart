# -*- coding: utf-8 -*-
"""Methods suggested to move in psychrolib (TEMPORALLY HERE)."""
from psychrolib import isIP, MIN_HUM_RATIO, R_DA_IP, R_DA_SI

# TODO Remove these when psychrolib 2.3.0 is released:
# Zero degree Fahrenheit (°F) expressed as degree Rankine (°R)
ZERO_FAHRENHEIT_AS_RANKINE = 459.67
# Zero degree Celsius (°C) expressed as Kelvin (K)
ZERO_CELSIUS_AS_KELVIN = 273.15


def GetTFahrenheitFromTRankine(TRankine: float) -> float:
    """
    Utility function to convert temperature to degree Fahrenheit (°F)
    given temperature in degree Rankine (°R).

    Args:
        TRankine: Temperature in degree Rankine (°R)

    Returns:
        Temperature in degree Fahrenheit (°F)

    Notes:
        Exact conversion.

    """
    return TRankine - ZERO_FAHRENHEIT_AS_RANKINE


def GetTCelsiusFromTKelvin(TKelvin: float) -> float:
    """
    Utility function to convert temperature to degree Celsius (°C)
    given temperature in Kelvin (K).

    Args:
        TKelvin: Temperature in Kelvin (K)

    Returns:
        Temperature in degree Celsius (°C)

    Notes:
        Exact conversion.

    """
    return TKelvin - ZERO_CELSIUS_AS_KELVIN


def GetTDryBulbFromMoistAirVolume(
    MoistAirVolume: float, HumRatio: float, Pressure: float
) -> float:
    """
    Return dry-bulb temperature given
    moist air specific volume, humidity ratio, and pressure.

    Args:
        MoistAirVolume: Specific volume of moist air
          in ft³ lb⁻¹ of dry air [IP] or in m³ kg⁻¹ of dry air [SI]
        HumRatio : Humidity ratio
          in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 26

    Notes:
        In IP units, R_DA_IP / 144 equals 0.370486 which is the coefficient
          appearing in eqn 26
        The factor 144 is for the conversion of Psi = lb in⁻² to lb ft⁻².
        Based on the `GetMoistAirVolume` function,
          rearranged for dry-bulb temperature.

    """
    if HumRatio < 0:  # pragma: no cover
        raise ValueError("Humidity ratio is negative")
    BoundedHumRatio = max(HumRatio, MIN_HUM_RATIO)

    if isIP():
        TDryBulb = GetTFahrenheitFromTRankine(
            MoistAirVolume
            * (144 * Pressure)
            / (R_DA_IP * (1 + 1.607858 * BoundedHumRatio))
        )
    else:
        TDryBulb = GetTCelsiusFromTKelvin(
            MoistAirVolume
            * Pressure
            / (R_DA_SI * (1 + 1.607858 * BoundedHumRatio))
        )
    return TDryBulb
