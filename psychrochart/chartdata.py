"""A library to make psychrometric charts and overlay information in them."""

import logging
from typing import Sequence

import numpy as np
from psychrolib import (
    GetHumRatioFromTWetBulb,
    GetHumRatioFromVapPres,
    GetMoistAirEnthalpy,
    GetMoistAirVolume,
    GetRelHumFromHumRatio,
    GetSatVapPres,
    GetTDewPointFromVapPres,
    GetTDryBulbFromEnthalpyAndHumRatio,
    GetTDryBulbFromMoistAirVolumeAndHumRatio,
    GetTWetBulbFromHumRatio,
    GetVapPresFromHumRatio,
    isIP,
)
from scipy.interpolate import interp1d

from psychrochart.models.curves import PsychroCurve, PsychroCurves
from psychrochart.models.styles import AnnotationStyle, CurveStyle
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


def _get_humid_ratio_in_saturation(
    dry_temps: np.ndarray, pressure: float
) -> np.array:
    sat_p = f_vec_sat_press(dry_temps)
    return _factor_out_w() * f_vec_hum_ratio_from_vap_press(sat_p, pressure)


def get_rh_max_min_in_limits(
    dbt_min: float,
    dbt_max: float,
    w_humidity_ratio_min: float,
    w_humidity_ratio_max: float,
    pressure: float,
) -> tuple[float, float]:
    """Get max range for constant rel. humidity lines inside chart limits."""
    rh_min = GetRelHumFromHumRatio(
        dbt_max, w_humidity_ratio_min / _factor_out_w(), pressure
    )
    rh_max = GetRelHumFromHumRatio(
        dbt_min, w_humidity_ratio_max / _factor_out_w(), pressure
    )
    return max(rh_min * 100.0, 0), min(rh_max * 100.0, 100)


def gen_points_in_constant_relative_humidity(
    dry_temps: Sequence[float],
    rh_percentage: float | Sequence[float],
    pressure: float,
) -> np.array:
    """Generate a curve (numpy array) of constant humidity ratio."""
    return _factor_out_w() * f_vec_hum_ratio_from_vap_press(
        f_vec_sat_press(dry_temps)
        * np.array(rh_percentage).clip(0, 100)
        / 100.0,
        pressure,
    )


def make_constant_relative_humidity_lines(
    dbt_min: float,
    dbt_max: float,
    temp_step: float,
    pressure: float,
    rh_perc_values: list[int],
    *,
    style: CurveStyle,
    rh_label_values: list[int] | None = None,
    label_loc: float = 0.0,
    family_label: str | None = None,
    annotation_style: AnnotationStyle | None = None,
) -> PsychroCurves:
    """Generate curves of constant relative humidity for the chart."""
    rh_values = sorted(rh for rh in rh_perc_values if 0 <= rh <= 100)
    temps_ct_rh = np.arange(dbt_min, dbt_max + temp_step, temp_step)
    curves_ct_rh = [
        gen_points_in_constant_relative_humidity(temps_ct_rh, rh, pressure)
        for rh in rh_values
    ]
    rh_label_values = rh_label_values or []
    return PsychroCurves(
        curves=[
            PsychroCurve(
                x_data=temps_ct_rh,
                y_data=curve_ct_rh,
                style=style,
                type_curve="constant_rh_data",
                label_loc=label_loc,
                label=f"RH {rh:g} %" if rh in rh_label_values else None,
                internal_value=float(rh),
                annotation_style=annotation_style,
            )
            for rh, curve_ct_rh in zip(rh_values, curves_ct_rh)
        ],
        family_label=family_label,
    )


def make_constant_dry_bulb_v_line(
    w_humidity_ratio_min: float,
    temp: float,
    pressure: float,
    *,
    style: CurveStyle,
    type_curve: str | None = None,
    reverse: bool = False,
    annotation_style: AnnotationStyle | None = None,
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
        internal_value=temp,
        annotation_style=annotation_style,
    )


def make_constant_dry_bulb_v_lines(
    w_humidity_ratio_min: float,
    pressure: float,
    temps_vl: np.ndarray,
    *,
    style: CurveStyle,
    family_label: str | None = None,
    annotation_style: AnnotationStyle | None = None,
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
                internal_value=temp,
                annotation_style=annotation_style,
            )
            for temp, w_max in zip(temps_vl, w_max_vec)
        ],
        family_label=family_label,
    )


def make_constant_humidity_ratio_h_lines(
    dbt_max: float,
    pressure: float,
    ws_hl: np.ndarray,
    *,
    style: CurveStyle,
    family_label: str | None = None,
    annotation_style: AnnotationStyle | None = None,
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
                internal_value=w,
                annotation_style=annotation_style,
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
    style: CurveStyle | None = None,
) -> PsychroCurve:
    """Generate line of saturation for the psychrochart."""
    temps_sat_line = np.arange(dbt_min, dbt_max + temp_step, temp_step)
    w_sat = gen_points_in_constant_relative_humidity(
        temps_sat_line, 100, pressure
    )
    return PsychroCurve(
        x_data=temps_sat_line,
        y_data=w_sat,
        style=style if style is not None else CurveStyle(),
        type_curve="saturation",
        internal_value=100.0,
    )


def make_constant_enthalpy_lines(
    w_humidity_ratio_min: float,
    pressure: float,
    enthalpy_values: np.ndarray,
    *,
    saturation_curve: PsychroCurve,
    style: CurveStyle,
    delta_t: float,
    h_label_values: list[float] | None = None,
    label_loc: float = 0.0,
    family_label: str | None = None,
    dbt_min_seen: float | None = None,
    annotation_style: AnnotationStyle | None = None,
) -> PsychroCurves | None:
    """Generate curves of constant enthalpy for the chart."""
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
    h_min = (
        GetMoistAirEnthalpy(
            dbt_min_seen or saturation_curve.x_data[0],
            w_humidity_ratio_min / _factor_out_w(),
        )
        / _factor_out_h()
    )
    h_max = h_in_sat[-1]
    h_objective = np.array([h for h in enthalpy_values if h_min < h < h_max])
    if not h_objective.shape[0]:
        logging.warning(
            "All %d enthalpy curves are outside limits"
            "(%g->%g not inside [%g, %g])",
            len(enthalpy_values),
            enthalpy_values[0],
            enthalpy_values[-1],
            h_min,
            h_max,
        )
        return None

    temps_max_constant_h = f_vec_dry_temp_from_enthalpy(
        h_objective * _factor_out_h(),
        w_humidity_ratio_min / _factor_out_w(),
    )
    t_sat_points = solve_curves_with_iteration(
        "ENTHALPHY",
        h_objective,
        lambda *x: t_sat_interpolator(x[0]),
        lambda x: GetMoistAirEnthalpy(
            x, GetHumRatioFromVapPres(GetSatVapPres(x), pressure)
        )
        / _factor_out_h(),
    )
    w_in_sat = _get_humid_ratio_in_saturation(t_sat_points, pressure)

    curves = [
        PsychroCurve(
            x_data=np.array([t_sat, t_max]),
            y_data=np.array([w_sat, w_humidity_ratio_min]),
            style=style,
            type_curve="constant_h_data",
            label_loc=label_loc,
            label=(
                _make_enthalpy_label(h)
                if isinstance(h_label_values, list)
                and round(h, 3) in h_label_values
                else None
            ),
            internal_value=round(h, 3),
            annotation_style=annotation_style,
        )
        for t_sat, w_sat, t_max, h in zip(
            t_sat_points, w_in_sat, temps_max_constant_h, h_objective
        )
    ]

    if label_loc < 0:
        style.linestyle = "--"
        curves += [
            PsychroCurve(
                x_data=np.array([t_sat + (delta_t * label_loc), t_sat]),
                y_data=np.array(
                    [
                        w_sat
                        + (delta_t * label_loc)
                        * (w_humidity_ratio_min - w_sat)
                        / (t_max - t_sat),
                        w_sat,
                    ]
                ),
                style=style,
                type_curve="constant_h_data",
                internal_value=round(h, 3),
            )
            for t_sat, w_sat, t_max, h, curve in zip(
                t_sat_points,
                w_in_sat,
                temps_max_constant_h,
                h_objective,
                curves,
            )
            if curve.label is not None
        ]

    return PsychroCurves(
        curves=curves,
        family_label=family_label,
    )


def make_constant_specific_volume_lines(
    w_humidity_ratio_min: float,
    pressure: float,
    vol_values: np.ndarray,
    *,
    saturation_curve: PsychroCurve,
    style: CurveStyle,
    v_label_values: list[float] | None = None,
    label_loc: float = 0.0,
    family_label: str | None = None,
    dbt_min_seen: float | None = None,
    annotation_style: AnnotationStyle | None = None,
) -> PsychroCurves | None:
    """Generate curves of constant specific volume for the chart."""
    v_in_sat = f_vec_moist_air_volume(
        saturation_curve.x_data,
        saturation_curve.y_data / _factor_out_w(),
        pressure,
    )
    v_min = GetMoistAirVolume(
        dbt_min_seen or saturation_curve.x_data[0],
        w_humidity_ratio_min / _factor_out_w(),
        pressure,
    )
    v_max = v_in_sat[-1]
    valid_objectives = [h for h in vol_values if v_min < h < v_max]
    if not valid_objectives:
        logging.warning(
            "All %d constant-volume curves are outside limits "
            "(%g->%g not inside [%g, %g])",
            len(vol_values),
            vol_values[0],
            vol_values[-1],
            v_min,
            v_max,
        )
        return None

    v_objective = np.array(valid_objectives)
    temps_max_constant_v = f_vec_dry_temp_from_spec_vol(
        np.array(v_objective), w_humidity_ratio_min / _factor_out_w(), pressure
    )
    t_sat_interpolator = interp1d(
        v_in_sat,
        saturation_curve.x_data,
        fill_value="extrapolate",
        assume_sorted=True,
    )
    t_sat_points = solve_curves_with_iteration(
        "CONSTANT VOLUME",
        v_objective,
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
                    if isinstance(v_label_values, list)
                    and round(vol, 3) in v_label_values
                    else None
                ),
                internal_value=round(vol, 3),
                annotation_style=annotation_style,
            )
            for t_sat, w_sat, t_max, vol in zip(
                t_sat_points, w_in_sat, temps_max_constant_v, v_objective
            )
        ],
        family_label=family_label,
    )


def make_constant_wet_bulb_temperature_lines(
    dry_bulb_temp_min: float,
    dry_bulb_temp_max: float,
    w_humidity_ratio_min: float,
    w_humidity_ratio_max: float,
    pressure: float,
    wbt_values: np.ndarray,
    *,
    style: CurveStyle,
    wbt_label_values: list[float] | None = None,
    label_loc: float = 0.0,
    family_label: str | None = None,
    annotation_style: AnnotationStyle | None = None,
) -> PsychroCurves | None:
    """Generate curves of constant wet bulb temperature for the chart."""
    wt_min = GetTWetBulbFromHumRatio(
        dry_bulb_temp_min, w_humidity_ratio_min / _factor_out_w(), pressure
    )
    if -0.75 < wt_min < 0.0:  # slope change zone
        wt_min = 0
    wt_bottom_right = GetTWetBulbFromHumRatio(dry_bulb_temp_max, 0, pressure)
    wt_top_right = GetTWetBulbFromHumRatio(
        dry_bulb_temp_max,
        min(
            w_humidity_ratio_max / _factor_out_w(),
            GetHumRatioFromVapPres(GetSatVapPres(dry_bulb_temp_max), pressure),
        ),
        pressure,
    )
    wbt_objective = np.array(
        [wt for wt in wbt_values if wt_min < wt < wt_top_right]
    )
    if wbt_objective.shape[0] == 0:
        logging.warning(
            "All %d wetbulb-temp curves are outside limits "
            "(%g->%g not inside [%g, %g])",
            len(wbt_values),
            wbt_values[0],
            wbt_values[-1],
            wt_min,
            dry_bulb_temp_max,
        )
        return None

    w_max_constant_wbt = f_vec_hum_ratio_from_vap_press(
        f_vec_sat_press(wbt_objective), pressure
    )
    curves = []
    for wbt, w_max in zip(wbt_objective, w_max_constant_wbt):
        dbt_objective = dry_bulb_temp_max
        w_left = _factor_out_w() * w_max
        if wbt >= wt_bottom_right:
            # on vertical y-axis
            w_right = _factor_out_w() * GetHumRatioFromTWetBulb(
                dbt_objective, wbt, pressure
            )
        else:
            # on horizontal x-axis
            dbt_objective = dry_bulb_temp_max
            w_right = _factor_out_w() * GetHumRatioFromTWetBulb(
                dbt_objective, wbt, pressure
            )
            while w_right <= 0.01:
                dbt_objective -= 0.5 * (dbt_objective - wbt)
                w_right = _factor_out_w() * GetHumRatioFromTWetBulb(
                    dbt_objective, wbt, pressure
                )
                if w_right > 0.01:
                    # extend curve to the bottom axis
                    slope = (dbt_objective - wbt) / (w_right - w_left)
                    dbt_objective = wbt - slope * w_left
                    w_right = 0.0
                    break

        c = PsychroCurve(
            x_data=np.array([wbt, dbt_objective]),
            y_data=np.array([w_left, w_right]),
            style=style,
            type_curve="constant_wbt_data",
            label_loc=label_loc,
            label=(
                _make_temp_label(wbt)
                if isinstance(wbt_label_values, list)
                and round(wbt, 3) in wbt_label_values
                else None
            ),
            internal_value=wbt,
            annotation_style=annotation_style,
        )
        curves.append(c)

    return PsychroCurves(curves=curves, family_label=family_label)
