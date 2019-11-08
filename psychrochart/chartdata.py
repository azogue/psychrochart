# -*- coding: utf-8 -*-
"""A library to make psychrometric charts and overlay information in them."""
from typing import Callable, Dict, Iterable, List, Tuple, Union

from psychrolib import (
    GetHumRatioFromVapPres,
    GetMoistAirEnthalpy,
    GetMoistAirVolume,
    GetRelHumFromTWetBulb,
    GetSatVapPres,
    GetTDewPointFromVapPres,
    GetTDryBulbFromEnthalpyAndHumRatio,
    GetUnitSystem,
    GetVapPresFromHumRatio,
    SetUnitSystem,
    SI,
)

from .psychrocurves import PsychroCurve, PsychroCurves
from .psychrolib_extra import GetTDryBulbFromMoistAirVolume
from .util import f_range, solve_curves_with_iteration

# Set SI unit system by default
if GetUnitSystem() is None:
    SetUnitSystem(SI)


def _gen_list_curves_range_temps(
    func_curve: Callable,
    curves_values: Iterable[float],
    dbt_min: float,
    dbt_max: float,
    increment: float,
    pressure: float,
) -> Tuple[List[float], List[List[float]]]:
    """Generate a curve from a range of temperatures."""
    temps = f_range(dbt_min, dbt_max + increment, increment)
    curves = [func_curve(temps, value, pressure) for value in curves_values]
    return temps, curves


def gen_points_in_constant_relative_humidity(
    dry_temps: Iterable[float],
    rh_percentage: Union[float, Iterable[float]],
    p_atm_kpa: float,
) -> List[float]:
    """Generate a curve (numpy array) of constant humidity ratio."""
    if isinstance(rh_percentage, Iterable):
        return [
            1000.0
            * humidity_ratio(
                saturation_pressure_water_vapor(t) * rh / 100.0, p_atm_kpa,
            )
            for t, rh in zip(dry_temps, rh_percentage)
        ]
    return [
        1000.0
        * humidity_ratio(
            saturation_pressure_water_vapor(t) * rh_percentage / 100.0,
            p_atm_kpa,
        )
        for t in dry_temps
    ]


def make_constant_relative_humidity_lines(
    dbt_min: float,
    dbt_max: float,
    temp_step: float,
    pressure: float,
    rh_perc_values: Iterable[float],
    rh_label_values: Iterable[float],
    style: dict,
    label_loc: float,
    family_label: str,
) -> PsychroCurves:
    """TODO doc for # Constant relative humidity curves:"""
    temps_ct_rh, curves_ct_rh = _gen_list_curves_range_temps(
        gen_points_in_constant_relative_humidity,
        rh_perc_values,
        dbt_min,
        dbt_max,
        temp_step,
        pressure,
    )
    return PsychroCurves(
        [
            PsychroCurve(
                temps_ct_rh,
                curve_ct_rh,
                style,
                type_curve="constant_rh_data",
                label_loc=label_loc,
                label=(
                    f"RH {rh:g} %" if round(rh, 1) in rh_label_values else None
                ),
            )
            for rh, curve_ct_rh in zip(rh_perc_values, curves_ct_rh)
        ],
        family_label=family_label,
    )


def make_constant_dry_bulb_v_line(
    w_humidity_ratio_min: float,
    temp: float,
    pressure: float,
    style: dict,
    type_curve: str = None,
    reverse: bool = False,
) -> PsychroCurve:
    """TODO doc for # Dry bulb constant line (vertical):"""
    w_max = 1000.0 * GetHumRatioFromVapPres(
        saturation_pressure_water_vapor(temp), pressure
    )
    if reverse:
        path_y = [w_max, w_humidity_ratio_min]
    else:
        path_y = [w_humidity_ratio_min, w_max]
    return PsychroCurve([temp, temp], path_y, style, type_curve=type_curve)


def make_constant_dry_bulb_v_lines(
    w_humidity_ratio_min: float,
    pressure: float,
    temps_vl: Iterable[float],
    style: dict,
    family_label: str,
) -> PsychroCurves:
    """TODO doc for # Dry bulb constant lines (vertical):"""
    return PsychroCurves(
        [
            make_constant_dry_bulb_v_line(
                w_humidity_ratio_min,
                temp,
                pressure,
                style=style,
                type_curve="constant_dry_temp_data",
            )
            for temp in temps_vl
        ],
        family_label=family_label,
    )


def make_constant_humidity_ratio_h_lines(
    dbt_max: float,
    pressure: float,
    ws_hl: Iterable[float],
    style: dict,
    family_label: str,
) -> PsychroCurves:
    """TODO doc for # Absolute humidity constant lines (horizontal):"""
    dew_points = solve_curves_with_iteration(
        "DEW POINT",
        [x / 1000.0 for x in ws_hl],
        lambda x: dew_point_temperature(
            dbt_max, water_vapor_pressure(x, pressure)
        ),
        lambda x: humidity_ratio(
            saturation_pressure_water_vapor(x), p_atm_kpa=pressure,
        ),
    )
    return PsychroCurves(
        [
            PsychroCurve(
                [t_dp, dbt_max],
                [w, w],
                style,
                type_curve="constant_humidity_data",
            )
            for w, t_dp in zip(ws_hl, dew_points)
        ],
        family_label=family_label,
    )


def make_saturation_line(
    dbt_min: float,
    dbt_max: float,
    temp_step: float,
    pressure: float,
    style: dict,
) -> PsychroCurves:
    """TODO doc for # Saturation line:"""
    temps_sat_line, w_sat_line = _gen_list_curves_range_temps(
        gen_points_in_constant_relative_humidity,
        [100],
        dbt_min,
        dbt_max,
        temp_step,
        pressure,
    )
    return PsychroCurves(
        [
            PsychroCurve(
                temps_sat_line, w_sat_line[0], style, type_curve="saturation",
            )
        ]
    )


def make_constant_enthalpy_lines(
    w_humidity_ratio_min: float,
    pressure: float,
    enthalpy_values: Iterable[float],
    h_label_values: Iterable[float],
    style: dict,
    label_loc: float,
    family_label: str,
) -> PsychroCurves:
    """TODO doc for # Constant enthalpy lines:"""
    temps_max_constant_h = [
        dry_temperature_for_enthalpy_of_moist_air(
            h, w_humidity_ratio_min / 1000.0
        )
        for h in enthalpy_values
    ]

    sat_points = solve_curves_with_iteration(
        "ENTHALPHY",
        enthalpy_values,
        lambda x: dry_temperature_for_enthalpy_of_moist_air(
            x, w_humidity_ratio_min / 1000.0
        ),
        lambda x: enthalpy_moist_air(
            x, saturation_pressure_water_vapor(x), p_atm_kpa=pressure,
        ),
    )

    return PsychroCurves(
        [
            PsychroCurve(
                [t_sat, t_max],
                [
                    1000.0
                    * humidity_ratio(
                        saturation_pressure_water_vapor(t_sat), pressure,
                    ),
                    w_humidity_ratio_min,
                ],
                style,
                type_curve="constant_h_data",
                label_loc=label_loc,
                label=(
                    f"{h:g} kJ/kg_da"
                    if round(h, 3) in h_label_values
                    else None
                ),
            )
            for t_sat, t_max, h in zip(
                sat_points, temps_max_constant_h, enthalpy_values
            )
        ],
        family_label=family_label,
    )


def make_constant_specific_volume_lines(
    pressure: float,
    vol_values: Iterable[float],
    v_label_values: Iterable[float],
    style: dict,
    label_loc: float,
    family_label: str,
) -> PsychroCurves:
    """TODO doc for # Constant specific volume lines:"""
    temps_max_constant_v = [
        dry_temperature_for_specific_volume_of_moist_air(
            0, specific_vol, p_atm_kpa=pressure
        )
        for specific_vol in vol_values
    ]
    sat_points = solve_curves_with_iteration(
        "CONSTANT VOLUME",
        vol_values,
        lambda x: dry_temperature_for_specific_volume_of_moist_air(
            0, x, p_atm_kpa=pressure
        ),
        lambda x: specific_volume(
            x, saturation_pressure_water_vapor(x), p_atm_kpa=pressure,
        ),
    )

    return PsychroCurves(
        [
            PsychroCurve(
                [t_sat, t_max],
                [
                    1000.0
                    * humidity_ratio(
                        saturation_pressure_water_vapor(t_sat), pressure,
                    ),
                    0.0,
                ],
                style,
                type_curve="constant_v_data",
                label_loc=label_loc,
                label=(
                    f"{vol:g} m3/kg_da"
                    if round(vol, 3) in v_label_values
                    else None
                ),
            )
            for t_sat, t_max, vol in zip(
                sat_points, temps_max_constant_v, vol_values
            )
        ],
        family_label=family_label,
    )


def make_constant_wet_bulb_temperature_lines(
    dry_bulb_temp_max: float,
    pressure: float,
    wbt_values: Iterable[float],
    wbt_label_values: Iterable[float],
    style: dict,
    label_loc: float,
    family_label: str,
) -> PsychroCurves:
    """TODO doc for # Constant wet bulb temperature lines:"""
    w_max_constant_wbt = [
        humidity_ratio(saturation_pressure_water_vapor(wbt), pressure)
        for wbt in wbt_values
    ]

    curves = []
    for wbt, w_max in zip(wbt_values, w_max_constant_wbt):

        def _get_dry_temp_for_constant_wet_temp(
            dbt, wbt, p_atm,
        ):
            return 1000.0 * humidity_ratio(
                saturation_pressure_water_vapor(dbt)
                * relative_humidity_from_temps(dbt, wbt, p_atm_kpa=p_atm),
                p_atm_kpa=p_atm,
            )

        points_t = [wbt, dry_bulb_temp_max]
        points_w = [
            1000.0 * w_max,
            _get_dry_temp_for_constant_wet_temp(points_t[1], wbt, pressure,),
        ]
        while points_w[1] <= 0.01:
            points_t[1] -= 0.5 * (points_t[1] - wbt)
            points_w[1] = _get_dry_temp_for_constant_wet_temp(
                points_t[1], wbt, pressure,
            )

            if points_w[1] > 0.01:
                # extend curve to the bottom axis
                slope = (points_t[1] - points_t[0]) / (
                    points_w[1] - points_w[0]
                )
                new_dbt = wbt - slope * points_w[0]
                points_t[1] = new_dbt
                points_w[1] = 0.0
                break

        c = PsychroCurve(
            points_t,
            points_w,
            style,
            type_curve="constant_wbt_data",
            label_loc=label_loc,
            label=(f"{wbt:g} °C" if wbt in wbt_label_values else None),
        )
        curves.append(c)

    return PsychroCurves(curves, family_label=family_label)


def _make_zone_dbt_rh(
    t_min: float,
    t_max: float,
    increment: float,
    rh_min: float,
    rh_max: float,
    p_atm_kpa: float,
    style: dict = None,
    label: str = None,
) -> PsychroCurve:
    """Generate points for zone between constant dry bulb temps and RH."""
    temps = f_range(t_min, t_max + increment, increment)
    curve_rh_up = gen_points_in_constant_relative_humidity(
        temps, rh_max, p_atm_kpa
    )
    curve_rh_down = gen_points_in_constant_relative_humidity(
        temps, rh_min, p_atm_kpa
    )
    abs_humid: List[float] = (
        curve_rh_up + curve_rh_down[::-1] + [curve_rh_up[0]]
    )
    temps_zone: List[float] = temps + temps[::-1] + [temps[0]]
    return PsychroCurve(
        temps_zone,
        abs_humid,
        style,
        type_curve="constant_rh_data",
        label=label,
    )


def make_zone_curve(
    zone_conf: Dict, increment: float, p_atm_kpa: float
) -> PsychroCurve:
    """Generate points for zone between constant dry bulb temps and RH."""
    if zone_conf["zone_type"] == "dbt-rh":
        t_min, t_max = zone_conf["points_x"]
        rh_min, rh_max = zone_conf["points_y"]
        return _make_zone_dbt_rh(
            t_min,
            t_max,
            increment,
            rh_min,
            rh_max,
            p_atm_kpa,
            zone_conf["style"],
            label=zone_conf.get("label"),
        )
    # elif zone_conf['zone_type'] == 'xy-points':
    else:
        return PsychroCurve(
            zone_conf["points_x"],
            zone_conf["points_y"],
            zone_conf["style"],
            type_curve="custom path",
            label=zone_conf.get("label"),
        )
    # elif zone_conf['zone_type'] == 'dbt-rh-points':
    # make conversion rh -> w


def water_vapor_pressure(w_kg_kga: float, p_atm_kpa: float) -> float:
    """Obtain the water vapor pressure from the humidity ratio (w_kg_kga)."""
    return GetVapPresFromHumRatio(w_kg_kga, p_atm_kpa * 1000.0) / 1000.0


def humidity_ratio(p_vapor_kpa: float, p_atm_kpa: float) -> float:
    """Obtain the humidity ratio from the water vapor pressure."""
    return GetHumRatioFromVapPres(p_vapor_kpa, p_atm_kpa)
    # return GetHumRatioFromVapPres(p_vapor_kpa * 1000.0, p_atm_kpa * 1000.0)


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
