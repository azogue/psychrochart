# -*- coding: utf-8 -*-
"""A library to make psychrometric charts and overlay information in them."""
from math import log, exp

from psychrochart.util import iter_solver


PRESSURE_STD_ATM_KPA = 101.325
DELTA_TEMP_C_TO_KELVIN = 273.15

# Eq. (1) 2009 ASHRAE Handbook—Fundamentals (SI)
GAS_CONSTANT_R_DA = 0.287042  # = 8314.472/28.966 kJ/(kg_da·K)
# Eq. (2) 2009 ASHRAE Handbook—Fundamentals (SI)
# GAS_CONSTANT_R_W = 461.524  # = 8314.472/18.015268 = J/(kgw·K)


def pressure_by_altitude(altitude_m: float) -> float:
    """Obtain the standard pressure for a certain sea level.

    Pressure by altitude, eq. (3) 2009 ASHRAE Handbook—Fundamentals (SI).
    """
    return PRESSURE_STD_ATM_KPA * (1 - 2.25577e-5 * altitude_m) ** 5.2559


def water_vapor_pressure(
        w_kg_kga: float, p_atm_kpa: float=PRESSURE_STD_ATM_KPA) -> float:
    """Obtain the water vapor pressure from the humidity ratio (w_kg_kga).

    kPa, eq (38)
    2009 ASHRAE Handbook—Fundamentals (SI).
    """
    humid_ratio_vap_pres = .621945
    p_vapor_kpa = p_atm_kpa * w_kg_kga / (humid_ratio_vap_pres + w_kg_kga)
    return p_vapor_kpa


def humidity_ratio(
        p_vapor_kpa: float, p_atm_kpa: float=PRESSURE_STD_ATM_KPA) -> float:
    """Obtain the humidity ratio from the water vapor pressure.

    kg water vapor / kg dry air, eq (22)
    2009 ASHRAE Handbook—Fundamentals (SI).
    """
    humid_ratio_vap_pres = .621945
    w_kg_kga = humid_ratio_vap_pres * p_vapor_kpa / (p_atm_kpa - p_vapor_kpa)
    return w_kg_kga


# TODO prec revision:
def humidity_ratio_from_temps(
        dry_bulb_temp_c: float, wet_bulb_temp_c: float,
        p_atm_kpa: float=PRESSURE_STD_ATM_KPA) -> float:
    """Obtain the specific humidity from the dry and wet bulb temperatures.

    kg water vapor / kg dry air, eqs (35) and (37)
    2009 ASHRAE Handbook—Fundamentals (SI).
    """
    w_sat_wet_bulb = humidity_ratio(
        saturation_pressure_water_vapor(wet_bulb_temp_c), p_atm_kpa)
    delta_t = dry_bulb_temp_c - wet_bulb_temp_c
    # assert (delta_t >= 0)
    factor_delta = 1.006 * delta_t
    if dry_bulb_temp_c > 0:
        num_1 = (2501 - 2.326 * wet_bulb_temp_c) * w_sat_wet_bulb
        denom_1 = 2501 + 1.86 * dry_bulb_temp_c - 4.186 * wet_bulb_temp_c
        w_kg_kga = (num_1 - factor_delta) / denom_1
    else:
        num_2 = (2830 - .24 * wet_bulb_temp_c) * w_sat_wet_bulb
        denom_2 = 2830 + 1.86 * dry_bulb_temp_c - 2.1 * wet_bulb_temp_c
        w_kg_kga = (num_2 - factor_delta) / denom_2
    return w_kg_kga


def relative_humidity_from_temps(
        dry_bulb_temp_c: float, wet_bulb_temp_c: float,
        p_atm_kpa: float=PRESSURE_STD_ATM_KPA) -> float:
    """Obtain the relative humidity from the dry and wet bulb temperatures.

    Ratio of the mole fraction of water vapor x_w in a given moist
    air sample to the mole fraction xws in an air sample
    saturated at the same temperature and pressure.

    Eq (24) 2009 ASHRAE Handbook—Fundamentals (SI).
    """
    w_kg_kga = humidity_ratio_from_temps(
        dry_bulb_temp_c, wet_bulb_temp_c, p_atm_kpa)
    p_w_vapor = water_vapor_pressure(w_kg_kga, p_atm_kpa)
    p_sat = saturation_pressure_water_vapor(dry_bulb_temp_c)
    return min(1., p_w_vapor / p_sat)


def specific_volume(
        dry_temp_c: float, p_vapor_kpa: float,
        p_atm_kpa: float=PRESSURE_STD_ATM_KPA) -> float:
    """Obtain the specific volume v of a moist air mixture.

    m3 / kg dry air, eq. (28) 2009 ASHRAE Handbook—Fundamentals (SI).
    """
    w_kg_kga = humidity_ratio(p_vapor_kpa, p_atm_kpa)
    specific_vol_m3_kga = (GAS_CONSTANT_R_DA
                           * (dry_temp_c + DELTA_TEMP_C_TO_KELVIN)
                           * (1 + 1.607858 * w_kg_kga) / p_atm_kpa)
    return specific_vol_m3_kga


def dry_temperature_for_specific_volume_of_moist_air(
        w_kg_kga: float, specific_vol: float,
        p_atm_kpa: float=PRESSURE_STD_ATM_KPA) -> float:
    """Solve the dry bulb temp from humidity ratio and specific volume.

    ºC. Derived from eq. (28), 2009 ASHRAE Handbook—Fundamentals (SI).
    """
    return (1741905.36576529 * p_atm_kpa * specific_vol
            / (803929. * w_kg_kga + 500000.) - DELTA_TEMP_C_TO_KELVIN)


def density_water_vapor(p_vapor_kpa: float, dry_bulb_temp_c: float) -> float:
    """Density of water vapor."""
    return (.0022 * p_vapor_kpa * 1000.
            / (dry_bulb_temp_c + DELTA_TEMP_C_TO_KELVIN))


def saturation_pressure_water_vapor(dry_temp_c: float, mode=3) -> float:
    """Saturation pressure of water vapor (kPa) from dry temperature.

    3 approximations:
      - mode 1: ASHRAE formulation
      - mode 2: Simpler, values for T > 0 / T < 0, but same speed as 1
      - mode 3: More simpler, near 2x vs mode 1.
    """
    if mode == 1:  # 2009 ASHRAE Handbook—Fundamentals (SI)
        abs_temp = dry_temp_c + DELTA_TEMP_C_TO_KELVIN
        if dry_temp_c > 0:  # Eq (6) 2009 ASHRAE Handbook—Fundamentals (SI)
            c1 = -5.8002206e3
            c2 = 1.3914993
            c3 = -4.8640239e-2
            c4 = 4.1764768e-5
            c5 = -1.4452093e-8
            c6 = 6.5459673
            ln_p_ws_pa = (c1 / abs_temp + c2 + c3 * abs_temp
                          + c4 * abs_temp ** 2 + c5 * abs_temp ** 3
                          + c6 * log(abs_temp))
        else:  # Eq (5) 2009 ASHRAE Handbook—Fundamentals (SI)
            c7 = -5.6745359e3
            c8 = 6.3925247
            c9 = -9.6778430e-3
            c10 = 6.2215701e-7
            c11 = 2.0747825e-9
            c12 = -9.4840240e-13
            c13 = 4.1635019
            ln_p_ws_pa = (c7 / abs_temp + c8 + c9 * abs_temp
                          + c10 * abs_temp ** 2 + c11 * abs_temp ** 3
                          + c12 * abs_temp ** 4 + c13 * log(abs_temp))
        return exp(ln_p_ws_pa) / 1000
    elif mode == 2:
        if dry_temp_c > 0:
            return 610.5 * exp(
                17.269 * dry_temp_c / (237.3 + dry_temp_c)) / 1000.
        else:
            return 610.5 * exp(
                21.875 * dry_temp_c / (265.5 + dry_temp_c)) / 1000.
    else:  # mode = 3
        return 19314560 * 10. ** (-1779.75 / (237.3 + dry_temp_c))


def enthalpy_moist_air(
        dry_temp_c: float, p_vapor_kpa: float,
        p_atm_kpa: float=PRESSURE_STD_ATM_KPA) -> float:
    """Moist air specific enthalpy.

    KJ / kg. Eqs. (32), (30), (31) 2009 ASHRAE Handbook—Fundamentals (SI).
    """
    w_kg_kga = humidity_ratio(p_vapor_kpa, p_atm_kpa)

    c_pa = 1.006  # kJ/(kg·ºC), sensible
    c_pv = 1.86  # kJ/(kg·ºC), latent
    # Evaporation heat (using constant value. For water at 0ºC, it's 2501)
    # constant_water_evaporation_heat = 2503  # KJ / kg
    constant_water_evaporation_heat = 2501  # KJ / kg

    h_a = c_pa * dry_temp_c
    h_v = w_kg_kga * (constant_water_evaporation_heat + c_pv * dry_temp_c)
    h_m = h_a + h_v
    return h_m


def dry_temperature_for_enthalpy_of_moist_air(
        w_kg_kga: float, enthalpy: float) -> float:
    """Solve the dry bulb temp from humidity ratio and specific enthalpy.

    ºC. Derived from eq. (32), 2009 ASHRAE Handbook—Fundamentals (SI).
    """
    return 500. * (enthalpy - 2501.0 * w_kg_kga) / (930.0 * w_kg_kga + 503.0)


def dew_point_temperature(p_w_kpa: float) -> float:
    """Dew point temperature.

    Eqs. (39) and (40) Peppers 1988
    2009 ASHRAE Handbook—Fundamentals (SI).
    """
    try:
        alpha = log(p_w_kpa)
    except ValueError:  # pragma: no cover
        raise AssertionError("Bad water vapor pressure! ({} kPa)"
                             .format(p_w_kpa))
    c14 = 6.54
    c15 = 14.526
    c16 = .7389
    c17 = .009486
    c18 = .4569
    dew_point = (c14 + c15 * alpha + c16 * alpha ** 2 + c17 * alpha ** 3
                 + c18 * p_w_kpa ** .1984)
    if dew_point < 0:
        # print('BAD dew_point: ', dew_point)
        dew_point = 6.09 + 12.608 * alpha + .4959 * alpha ** 2
        # print('GOOD dew_point: ', dew_point)
    return dew_point


def wet_bulb_temperature(
        dry_temp_c: float, relative_humid: float,
        p_atm_kpa: float=PRESSURE_STD_ATM_KPA,
        num_iters_max=100, precision=0.00001) -> float:
    """Wet bulb temperature.

    Requires trial-and-error or numerical solution method
    applying eqs. (23) and (35) or (37)
    2009 ASHRAE Handbook—Fundamentals (SI).
    """
    out = iter_solver(
        dry_temp_c - 10, relative_humid,
        lambda x: relative_humidity_from_temps(
            dry_temp_c, x, p_atm_kpa=p_atm_kpa),
        initial_increment=0.5,
        num_iters_max=num_iters_max, precision=precision)

    # Wet bulb temperature can't be greater than dry bulb temp:
    if out > dry_temp_c:
        out = dry_temp_c
    return out

# def degree_of_saturation(w_kg_kga, wsat_kg_kga):
#     """Ratio of air humidity ratio to humidity ratio of saturated moist air.
#
#     µ (no dimension), eq (12) 2009 ASHRAE Handbook—Fundamentals (SI).
#     """
#     return w_kg_kga / wsat_kg_kga
#
#
# def relative_humidity(p_vapor_kpa, p_sat_vapor_kpa):
#     """Ratio of the mole fraction of water vapor x_w in a given moist
#     air sample to the mole fraction xws in an air sample
#     saturated at the same temperature and pressure.
#
#     Eq (24) 2009 ASHRAE Handbook—Fundamentals (SI).
#     """
#     return p_vapor_kpa / p_sat_vapor_kpa
