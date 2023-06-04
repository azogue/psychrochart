"""A library to make psychrometric charts and overlay information in them."""
from typing import Callable, Iterable

import numpy as np
from psychrolib import (
    GetHumRatioFromVapPres,
    GetMoistAirEnthalpy,
    GetMoistAirVolume,
    GetRelHumFromTWetBulb,
    GetSatVapPres,
    GetTDewPointFromVapPres,
    GetTDryBulbFromEnthalpyAndHumRatio,
    GetTDryBulbFromMoistAirVolumeAndHumRatio,
    GetVapPresFromHumRatio,
    isIP,
)
from scipy.interpolate import interp1d

from psychrochart.models.annots import ChartZone
from psychrochart.models.curves import PsychroCurve, PsychroCurves
from psychrochart.models.styles import CurveStyle, ZoneStyle
from psychrochart.util import solve_curves_with_iteration

f_vec_hum_ratio_from_vap_press = np.vectorize(GetHumRatioFromVapPres)
f_vec_moist_air_enthalpy = np.vectorize(GetMoistAirEnthalpy)
f_vec_moist_air_volume = np.vectorize(GetMoistAirVolume)
f_vec_dew_point_from_vap_press = np.vectorize(GetTDewPointFromVapPres)
f_vec_dry_temp_from_enthalpy = np.vectorize(GetTDryBulbFromEnthalpyAndHumRatio)
f_vec_dry_temp_from_spec_vol = np.vectorize(
    GetTDryBulbFromMoistAirVolumeAndHumRatio
)
f_vec_sat_press = np.vectorize(GetSatVapPres)
f_vec_vap_press_from_hum_ratio = np.vectorize(GetVapPresFromHumRatio)


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
) -> tuple[np.array, list[np.array]]:
    """Generate a curve from a range of temperatures."""
    temps = np.arange(dbt_min, dbt_max + increment, increment)
    curves = [func_curve(temps, value, pressure) for value in curves_values]
    return temps, curves


def _get_humid_ratio_in_saturation(
    dry_temps: np.ndarray, pressure: float
) -> np.array:
    sat_p = f_vec_sat_press(dry_temps)
    return _factor_out_w() * f_vec_hum_ratio_from_vap_press(sat_p, pressure)


def gen_points_in_constant_relative_humidity(
    dry_temps: Iterable[float],
    rh_percentage: float | Iterable[float],
    pressure: float,
) -> np.array:
    """Generate a curve (numpy array) of constant humidity ratio."""
    return _factor_out_w() * f_vec_hum_ratio_from_vap_press(
        f_vec_sat_press(dry_temps) * np.array(rh_percentage) / 100.0, pressure
    )


def make_constant_relative_humidity_lines(
    dbt_min: float,
    dbt_max: float,
    temp_step: float,
    pressure: float,
    rh_perc_values: Iterable[float],
    rh_label_values: Iterable[float],
    style: CurveStyle,
    label_loc: float,
    family_label: str | None,
) -> PsychroCurves:
    """Generate curves of constant relative humidity for the chart."""
    temps_ct_rh, curves_ct_rh = _gen_list_curves_range_temps(
        gen_points_in_constant_relative_humidity,
        rh_perc_values,
        dbt_min,
        dbt_max,
        temp_step,
        pressure,
    )
    return PsychroCurves(
        curves=[
            PsychroCurve(
                x_data=temps_ct_rh,
                y_data=curve_ct_rh,
                style=style,
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
    style: CurveStyle,
    type_curve: str | None = None,
    reverse: bool = False,
) -> PsychroCurve:
    """Generate vertical line (constant dry bulb temp) up to saturation."""
    w_max = _factor_out_w() * GetHumRatioFromVapPres(
        GetSatVapPres(temp), pressure
    )
    if reverse:
        path_y = [w_max, w_humidity_ratio_min]
    else:
        path_y = [w_humidity_ratio_min, w_max]
    return PsychroCurve(
        x_data=np.array([temp, temp]),
        y_data=np.array(path_y),
        style=style,
        type_curve=type_curve,
    )


def make_constant_dry_bulb_v_lines(
    w_humidity_ratio_min: float,
    pressure: float,
    temps_vl: np.ndarray,
    style: CurveStyle,
    family_label: str | None,
) -> PsychroCurves:
    """Generate curves of constant dry bulb temperature (vertical)."""
    w_max_vec = _get_humid_ratio_in_saturation(temps_vl, pressure)
    return PsychroCurves(
        curves=[
            PsychroCurve(
                x_data=np.array([temp, temp]),
                y_data=np.array([w_humidity_ratio_min, w_max]),
                style=style,
                type_curve="constant_dry_temp_data",
            )
            for temp, w_max in zip(temps_vl, w_max_vec)
        ],
        family_label=family_label,
    )


def make_constant_humidity_ratio_h_lines(
    dbt_max: float,
    pressure: float,
    ws_hl: Iterable[float],
    style: CurveStyle,
    family_label: str | None,
) -> PsychroCurves:
    """Generate curves of constant absolute humidity (horizontal)."""
    arr_hum_ratios = np.array(ws_hl) / _factor_out_w()
    dew_points = f_vec_dew_point_from_vap_press(
        dbt_max, f_vec_vap_press_from_hum_ratio(arr_hum_ratios, pressure)
    )
    return PsychroCurves(
        curves=[
            PsychroCurve(
                x_data=np.array([t_dp, dbt_max]),
                y_data=np.array([w, w]),
                style=style,
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
    style: CurveStyle,
) -> PsychroCurves:
    """Generate line of saturation for the psychrochart."""
    temps_sat_line = np.arange(dbt_min, dbt_max + temp_step, temp_step)
    w_sat = gen_points_in_constant_relative_humidity(
        temps_sat_line, 100.0, pressure
    )
    sat_c = PsychroCurve(
        x_data=temps_sat_line,
        y_data=w_sat,
        style=style,
        type_curve="saturation",
    )
    return PsychroCurves(curves=[sat_c])


def make_constant_enthalpy_lines(
    w_humidity_ratio_min: float,
    pressure: float,
    enthalpy_values: Iterable[float],
    h_label_values: Iterable[float],
    style: CurveStyle,
    label_loc: float,
    family_label: str | None,
    saturation_curve: PsychroCurve,
) -> PsychroCurves:
    """Generate curves of constant enthalpy for the chart."""
    enthalpy_objective = np.array(enthalpy_values)
    temps_max_constant_h = f_vec_dry_temp_from_enthalpy(
        enthalpy_objective * _factor_out_h(),
        w_humidity_ratio_min / _factor_out_w(),
    )
    h_in_sat = (
        f_vec_moist_air_enthalpy(
            saturation_curve.x_data, saturation_curve.y_data / _factor_out_w()
        )
        / _factor_out_h()
    )
    t_sat_interpolator = interp1d(
        h_in_sat,
        saturation_curve.x_data,
        fill_value="extrapolate",
        assume_sorted=True,
    )
    t_sat_points = solve_curves_with_iteration(
        "ENTHALPHY",
        enthalpy_objective,
        lambda *x: t_sat_interpolator(x[0]),
        lambda x: GetMoistAirEnthalpy(
            x, GetHumRatioFromVapPres(GetSatVapPres(x), pressure)
        )
        / _factor_out_h(),
    )
    w_in_sat = _get_humid_ratio_in_saturation(t_sat_points, pressure)

    return PsychroCurves(
        curves=[
            PsychroCurve(
                x_data=np.array([t_sat, t_max]),
                y_data=np.array([w_sat, w_humidity_ratio_min]),
                style=style,
                type_curve="constant_h_data",
                label_loc=label_loc,
                label=(
                    _make_enthalpy_label(h)
                    if round(h, 3) in h_label_values
                    else None
                ),
            )
            for t_sat, w_sat, t_max, h in zip(
                t_sat_points, w_in_sat, temps_max_constant_h, enthalpy_values
            )
        ],
        family_label=family_label,
    )


def make_constant_specific_volume_lines(
    w_humidity_ratio_min: float,
    pressure: float,
    vol_values: np.ndarray,
    v_label_values: Iterable[float],
    style: CurveStyle,
    label_loc: float,
    family_label: str | None,
    saturation_curve: PsychroCurve,
) -> PsychroCurves:
    """Generate curves of constant specific volume for the chart."""
    temps_max_constant_v = f_vec_dry_temp_from_spec_vol(
        np.array(vol_values), w_humidity_ratio_min / _factor_out_w(), pressure
    )
    v_in_sat = f_vec_moist_air_volume(
        saturation_curve.x_data,
        saturation_curve.y_data / _factor_out_w(),
        pressure,
    )
    t_sat_interpolator = interp1d(
        v_in_sat,
        saturation_curve.x_data,
        fill_value="extrapolate",
        assume_sorted=True,
    )
    t_sat_points = solve_curves_with_iteration(
        "CONSTANT VOLUME",
        vol_values,
        lambda *x: t_sat_interpolator(x[0]),
        lambda x: GetMoistAirVolume(
            x, GetHumRatioFromVapPres(GetSatVapPres(x), pressure), pressure
        ),
    )
    w_in_sat = _get_humid_ratio_in_saturation(t_sat_points, pressure)

    return PsychroCurves(
        curves=[
            PsychroCurve(
                x_data=np.array([t_sat, t_max]),
                y_data=np.array([w_sat, w_humidity_ratio_min]),
                style=style,
                type_curve="constant_v_data",
                label_loc=label_loc,
                label=(
                    _make_vol_label(vol)
                    if round(vol, 3) in v_label_values
                    else None
                ),
            )
            for t_sat, w_sat, t_max, vol in zip(
                t_sat_points, w_in_sat, temps_max_constant_v, vol_values
            )
        ],
        family_label=family_label,
    )


def make_constant_wet_bulb_temperature_lines(
    dry_bulb_temp_max: float,
    pressure: float,
    wbt_values: np.ndarray,
    wbt_label_values: Iterable[float],
    style: CurveStyle,
    label_loc: float,
    family_label: str | None,
) -> PsychroCurves:
    """Generate curves of constant wet bulb temperature for the chart."""
    w_max_constant_wbt = f_vec_hum_ratio_from_vap_press(
        f_vec_sat_press(np.array(wbt_values)), pressure
    )

    def _hum_ratio_for_constant_wet_temp_at_dry_temp(db_t, wb_t, p_atm):
        return _factor_out_w() * GetHumRatioFromVapPres(
            GetSatVapPres(db_t) * GetRelHumFromTWetBulb(db_t, wb_t, p_atm),
            p_atm,
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
            x_data=np.array(pair_t),
            y_data=np.array(pair_w),
            style=style,
            type_curve="constant_wbt_data",
            label_loc=label_loc,
            label=(_make_temp_label(wbt) if wbt in wbt_label_values else None),
        )
        curves.append(c)

    return PsychroCurves(curves=curves, family_label=family_label)


def _make_zone_dbt_rh(
    t_min: float,
    t_max: float,
    increment: float,
    rh_min: float,
    rh_max: float,
    pressure: float,
    style: ZoneStyle,
    label: str | None = None,
) -> PsychroCurve:
    """Generate points for zone between constant dry bulb temps and RH."""
    temps = np.arange(t_min, t_max + increment, increment)
    curve_rh_up = gen_points_in_constant_relative_humidity(
        temps, rh_max, pressure
    )
    curve_rh_down = gen_points_in_constant_relative_humidity(
        temps, rh_min, pressure
    )
    abs_humid: list[float] = (
        list(curve_rh_up) + list(curve_rh_down)[::-1] + [curve_rh_up[0]]
    )
    temps_zone: list[float] = list(temps) + list(temps)[::-1] + [temps[0]]
    return PsychroCurve(
        x_data=np.array(temps_zone),
        y_data=np.array(abs_humid),
        style=style,
        type_curve="constant_rh_data",
        label=label,
    )


def make_zone_curve(
    zone_conf: ChartZone, increment: float, pressure: float
) -> PsychroCurve:
    """Generate points for zone between constant dry bulb temps and RH."""
    # TODO make conversion rh -> w and new zone_type: "dbt-rh-points"
    assert isinstance(zone_conf.style, ZoneStyle)
    if zone_conf.zone_type == "dbt-rh":
        t_min = zone_conf.points_x[0]
        t_max = zone_conf.points_x[-1]
        rh_min = zone_conf.points_y[0]
        rh_max = zone_conf.points_y[-1]
        return _make_zone_dbt_rh(
            t_min,
            t_max,
            increment,
            rh_min,
            rh_max,
            pressure,
            zone_conf.style,
            label=zone_conf.label,
        )
    else:
        # zone_type: 'xy-points'
        return PsychroCurve(
            x_data=zone_conf.points_x,
            y_data=zone_conf.points_y,
            style=zone_conf.style,
            type_curve="custom path",
            label=zone_conf.label,
        )
