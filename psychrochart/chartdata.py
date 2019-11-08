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
    GetVapPresFromHumRatio,
    isIP,
)

from .psychrocurves import PsychroCurve, PsychroCurves
from .psychrolib_extra import GetTDryBulbFromMoistAirVolume
from .util import f_range, solve_curves_with_iteration


def _factor_out_w() -> float:
    """
    Conversion factor from internal units to plot units for humidity ratio.

    In SI, w is internally in kg(w)/kg(da), but for plots we use g(w)/kg(da).
    """
    return 7000.0 if isIP() else 1000.0


def _factor_out_h() -> float:
    """
    Conversion factor from internal units to plot units for enthalpy.

    In SI, h is internally in J/kg, but for plots we use kJ/kg.
    """
    return 1.0 if isIP() else 1000.0


def _make_enthalpy_label(enthalpy: float) -> str:
    unit = "$Btu/lb_{da}$" if isIP() else "$kJ/kg_{da}$"
    return f"{enthalpy:g} {unit}"


def _make_temp_label(temperature: float) -> str:
    unit = "°F" if isIP() else "°C"
    return f"{temperature:g} {unit}"


def _make_vol_label(specific_vol: float) -> str:
    unit = "$ft³/lb_{da}$" if isIP() else "$m³/kg_{da}$"
    return f"{specific_vol:g} {unit}"


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
    pressure: float,
) -> List[float]:
    """Generate a curve (numpy array) of constant humidity ratio."""
    if isinstance(rh_percentage, Iterable):
        return [
            _factor_out_w()
            * GetHumRatioFromVapPres(GetSatVapPres(t) * rh / 100.0, pressure)
            for t, rh in zip(dry_temps, rh_percentage)
        ]
    return [
        _factor_out_w()
        * GetHumRatioFromVapPres(
            GetSatVapPres(t) * rh_percentage / 100.0, pressure,
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
    w_max = _factor_out_w() * GetHumRatioFromVapPres(
        GetSatVapPres(temp), pressure
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
        [x / _factor_out_w() for x in ws_hl],
        lambda x: GetTDewPointFromVapPres(
            dbt_max, GetVapPresFromHumRatio(x, pressure)
        ),
        lambda x: GetHumRatioFromVapPres(GetSatVapPres(x), pressure),
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
        GetTDryBulbFromEnthalpyAndHumRatio(
            h * _factor_out_h(), w_humidity_ratio_min / _factor_out_w()
        )
        for h in enthalpy_values
    ]

    sat_points = solve_curves_with_iteration(
        "ENTHALPHY",
        enthalpy_values,
        lambda x: GetTDryBulbFromEnthalpyAndHumRatio(
            x * _factor_out_h(), w_humidity_ratio_min / _factor_out_w()
        ),
        lambda x: GetMoistAirEnthalpy(
            x, GetHumRatioFromVapPres(GetSatVapPres(x), pressure),
        )
        / _factor_out_h(),
    )

    return PsychroCurves(
        [
            PsychroCurve(
                [t_sat, t_max],
                [
                    _factor_out_w()
                    * GetHumRatioFromVapPres(GetSatVapPres(t_sat), pressure),
                    w_humidity_ratio_min,
                ],
                style,
                type_curve="constant_h_data",
                label_loc=label_loc,
                label=(
                    _make_enthalpy_label(h)
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
        GetTDryBulbFromMoistAirVolume(specific_vol, 0, pressure)
        for specific_vol in vol_values
    ]
    sat_points = solve_curves_with_iteration(
        "CONSTANT VOLUME",
        vol_values,
        lambda x: GetTDryBulbFromMoistAirVolume(x, 0, pressure),
        lambda x: GetMoistAirVolume(
            x, GetHumRatioFromVapPres(GetSatVapPres(x), pressure), pressure,
        ),
    )

    return PsychroCurves(
        [
            PsychroCurve(
                [t_sat, t_max],
                [
                    _factor_out_w()
                    * GetHumRatioFromVapPres(GetSatVapPres(t_sat), pressure),
                    0.0,
                ],
                style,
                type_curve="constant_v_data",
                label_loc=label_loc,
                label=(
                    _make_vol_label(vol)
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
        GetHumRatioFromVapPres(GetSatVapPres(wbt), pressure)
        for wbt in wbt_values
    ]

    def _hum_ratio_for_constant_wet_temp_at_dry_temp(dbt, wbt, p_atm):
        return _factor_out_w() * GetHumRatioFromVapPres(
            GetSatVapPres(dbt) * GetRelHumFromTWetBulb(dbt, wbt, p_atm), p_atm
        )

    curves = []
    for wbt, w_max in zip(wbt_values, w_max_constant_wbt):
        pair_t = [wbt, dry_bulb_temp_max]
        pair_w = [
            _factor_out_w() * w_max,
            _hum_ratio_for_constant_wet_temp_at_dry_temp(
                pair_t[1], wbt, pressure
            ),
        ]
        while pair_w[1] <= 0.01:
            pair_t[1] -= 0.5 * (pair_t[1] - wbt)
            pair_w[1] = _hum_ratio_for_constant_wet_temp_at_dry_temp(
                pair_t[1], wbt, pressure
            )

            if pair_w[1] > 0.01:
                # extend curve to the bottom axis
                slope = (pair_t[1] - pair_t[0]) / (pair_w[1] - pair_w[0])
                new_dbt = wbt - slope * pair_w[0]
                pair_t[1] = new_dbt
                pair_w[1] = 0.0
                break

        c = PsychroCurve(
            pair_t,
            pair_w,
            style,
            type_curve="constant_wbt_data",
            label_loc=label_loc,
            label=(_make_temp_label(wbt) if wbt in wbt_label_values else None),
        )
        curves.append(c)

    return PsychroCurves(curves, family_label=family_label)


def _make_zone_dbt_rh(
    t_min: float,
    t_max: float,
    increment: float,
    rh_min: float,
    rh_max: float,
    pressure: float,
    style: dict = None,
    label: str = None,
) -> PsychroCurve:
    """Generate points for zone between constant dry bulb temps and RH."""
    temps = f_range(t_min, t_max + increment, increment)
    curve_rh_up = gen_points_in_constant_relative_humidity(
        temps, rh_max, pressure
    )
    curve_rh_down = gen_points_in_constant_relative_humidity(
        temps, rh_min, pressure
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
    zone_conf: Dict, increment: float, pressure: float
) -> PsychroCurve:
    """Generate points for zone between constant dry bulb temps and RH."""
    # TODO make conversion rh -> w and new zone_type: "dbt-rh-points"
    if zone_conf["zone_type"] == "dbt-rh":
        t_min, t_max = zone_conf["points_x"]
        rh_min, rh_max = zone_conf["points_y"]
        return _make_zone_dbt_rh(
            t_min,
            t_max,
            increment,
            rh_min,
            rh_max,
            pressure,
            zone_conf["style"],
            label=zone_conf.get("label"),
        )
    else:
        # zone_type: 'xy-points'
        return PsychroCurve(
            zone_conf["points_x"],
            zone_conf["points_y"],
            zone_conf["style"],
            type_curve="custom path",
            label=zone_conf.get("label"),
        )
