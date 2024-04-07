import logging
from typing import Callable

import numpy as np
from psychrolib import (
    GetHumRatioFromVapPres,
    GetMoistAirVolume,
    GetSatAirEnthalpy,
    GetSatVapPres,
)

from psychrochart.chart_entities import random_internal_value
from psychrochart.chartdata import (
    _factor_out_h,
    _factor_out_w,
    f_vec_moist_air_enthalpy,
    f_vec_moist_air_volume,
    gen_points_in_constant_relative_humidity,
    make_constant_enthalpy_lines,
    make_constant_relative_humidity_lines,
    make_constant_specific_volume_lines,
    make_saturation_line,
)
from psychrochart.models.config import ChartZone
from psychrochart.models.curves import PsychroCurve, PsychroCurves
from psychrochart.models.styles import CurveStyle, ZoneStyle


def _adjust_temp_range_for_enthalpy(
    h_range: tuple[float, float],
    dbt_range: tuple[float, float],
    pressure: float,
    step_temp: float,
) -> float:
    assert h_range[1] > h_range[0]
    assert dbt_range[1] > dbt_range[0]
    dbt_min = dbt_range[0]
    while GetSatAirEnthalpy(dbt_min, pressure) * _factor_out_h() > h_range[0]:
        dbt_min -= 2 * step_temp
    return dbt_min


def _adjust_temp_range_for_volume(
    v_range: tuple[float, float],
    dbt_range: tuple[float, float],
    pressure: float,
    step_temp: float,
) -> float:
    assert v_range[1] > v_range[0]
    assert dbt_range[1] > dbt_range[0]
    dbt_min = dbt_range[0]
    while (
        GetMoistAirVolume(
            dbt_min,
            _factor_out_w()
            * GetHumRatioFromVapPres(GetSatVapPres(dbt_min), pressure),
            pressure,
        )
        > v_range[0]
    ):
        dbt_min -= 2 * step_temp
    return dbt_min


def _crossing_point_between_rect_lines(
    segment_1_x: tuple[float, float],
    segment_1_y: tuple[float, float],
    segment_2_x: tuple[float, float],
    segment_2_y: tuple[float, float],
):
    s1 = (segment_1_y[1] - segment_1_y[0]) / (segment_1_x[1] - segment_1_x[0])
    b1 = segment_1_y[0] - s1 * segment_1_x[0]

    s2 = (segment_2_y[1] - segment_2_y[0]) / (segment_2_x[1] - segment_2_x[0])
    b2 = segment_2_y[0] - s2 * segment_2_x[0]

    mat_a = np.array([[s1, -1], [s2, -1]])
    v_b = np.array([-b1, -b2])
    return np.linalg.solve(mat_a, v_b)


def _cross_rh_curve_with_rect_line(
    rh_curve: PsychroCurve,
    rect_curve: PsychroCurve,
    target_value: float,
    func_dbt_w_to_target: Callable[[np.ndarray, np.ndarray], np.ndarray],
) -> tuple[float, float]:
    assert len(rect_curve.x_data) == 2
    assert len(rect_curve.y_data) == 2

    target_in_rh = func_dbt_w_to_target(
        rh_curve.x_data, rh_curve.y_data / _factor_out_w()
    )
    # dbt_base should include crossing place
    assert target_in_rh[0] < target_value
    idx_end = (target_in_rh > target_value).argmax()
    if target_in_rh[-1] < target_value:
        # extrapolate last segment
        idx_end = -1
    t_start, t_end = rh_curve.x_data[idx_end - 1], rh_curve.x_data[idx_end]
    w_start, w_end = rh_curve.y_data[idx_end - 1], rh_curve.y_data[idx_end]
    return _crossing_point_between_rect_lines(
        segment_1_x=(rect_curve.x_data[0], rect_curve.x_data[1]),
        segment_1_y=(rect_curve.y_data[0], rect_curve.y_data[1]),
        segment_2_x=(t_start, t_end),
        segment_2_y=(w_start, w_end),
    )


def _valid_zone_delimiter_on_plot_limits(
    zone: ChartZone,
    rect_lines: PsychroCurves | None,
    dbt_min: float,
    dbt_max: float,
    w_min: float,
    w_max: float,
) -> bool:
    if (
        rect_lines is None
        or len(rect_lines.curves) != 2
        or all(
            curve.outside_limits(dbt_min, dbt_max, w_min, w_max)
            for curve in rect_lines.curves
        )
    ):
        logging.info("Zone[%s,%s] outside limits", zone.zone_type, zone.label)
        return False
    return True


def _zone_between_rh_and_rects(
    zone: ChartZone,
    rect_lines: PsychroCurves | None,
    rh_lines: PsychroCurves,
    func_dbt_w_to_target: Callable[[np.ndarray, np.ndarray], np.ndarray],
) -> PsychroCurve:
    assert rect_lines is not None
    target_min = rect_lines.curves[0].internal_value
    target_max = rect_lines.curves[1].internal_value
    assert target_min is not None and target_max is not None
    dbt_bottom_left, w_bottom_left = _cross_rh_curve_with_rect_line(
        rh_curve=rh_lines.curves[0],
        rect_curve=rect_lines.curves[0],
        target_value=target_min,
        func_dbt_w_to_target=func_dbt_w_to_target,
    )
    dbt_bottom_right, w_bottom_right = _cross_rh_curve_with_rect_line(
        rh_curve=rh_lines.curves[0],
        rect_curve=rect_lines.curves[1],
        target_value=target_max,
        func_dbt_w_to_target=func_dbt_w_to_target,
    )
    dbt_top_left, w_top_left = _cross_rh_curve_with_rect_line(
        rh_curve=rh_lines.curves[1],
        rect_curve=rect_lines.curves[0],
        target_value=target_min,
        func_dbt_w_to_target=func_dbt_w_to_target,
    )
    dbt_top_right, w_top_right = _cross_rh_curve_with_rect_line(
        rh_curve=rh_lines.curves[1],
        rect_curve=rect_lines.curves[1],
        target_value=target_max,
        func_dbt_w_to_target=func_dbt_w_to_target,
    )

    mask_rh_up = (rh_lines.curves[1].y_data < w_top_right) & (
        rh_lines.curves[1].y_data > w_top_left
    )
    mask_rh_down = (rh_lines.curves[0].y_data < w_bottom_right) & (
        rh_lines.curves[0].y_data > w_bottom_left
    )
    dbt_points = [
        dbt_top_left,
        *rh_lines.curves[1].x_data[mask_rh_up],
        dbt_top_right,
        dbt_bottom_right,
        *rh_lines.curves[0].x_data[mask_rh_down][::-1],
        dbt_bottom_left,
        dbt_top_left,
    ]
    w_points = [
        w_top_left,
        *rh_lines.curves[1].y_data[mask_rh_up],
        w_top_right,
        w_bottom_right,
        *rh_lines.curves[0].y_data[mask_rh_down][::-1],
        w_bottom_left,
        w_top_left,
    ]
    return PsychroCurve(
        x_data=np.array(dbt_points),
        y_data=np.array(w_points),
        style=zone.style,
        type_curve=zone.zone_type,
        label=zone.label,
        internal_value=random_internal_value() if zone.label is None else None,
        annotation_style=zone.annotation_style,
    )


def _make_zone_delimited_by_enthalpy_and_rh(
    zone: ChartZone,
    pressure: float,
    *,
    step_temp: float,
    dbt_min: float,
    dbt_max: float,
    w_min: float,
    w_max: float,
) -> PsychroCurve | None:
    assert zone.zone_type == "enthalpy-rh"
    h_min, h_max = zone.points_x
    rh_min, rh_max = zone.points_y
    delta_t = dbt_max - dbt_min
    dbt_min_use = _adjust_temp_range_for_enthalpy(
        (h_min, h_max), (dbt_min, dbt_max), pressure, step_temp
    )
    h_lines = make_constant_enthalpy_lines(
        w_min,
        pressure,
        np.array([h_min, h_max]),
        saturation_curve=make_saturation_line(
            dbt_min_use, dbt_max, step_temp, pressure
        ),
        style=CurveStyle(),
        delta_t=delta_t,
    )
    if not _valid_zone_delimiter_on_plot_limits(
        zone, h_lines, dbt_min, dbt_max, w_min, w_max
    ):
        return None

    rh_lines = make_constant_relative_humidity_lines(
        dbt_min_use,
        dbt_max,
        step_temp,
        pressure,
        [int(rh_min), int(rh_max)],
        style=CurveStyle(),
    )

    def _points_to_enthalpy(dbt_values, w_values):
        return f_vec_moist_air_enthalpy(dbt_values, w_values) / _factor_out_h()

    return _zone_between_rh_and_rects(
        zone,
        rect_lines=h_lines,
        rh_lines=rh_lines,
        func_dbt_w_to_target=_points_to_enthalpy,
    )


def _make_zone_delimited_by_vertical_dbt_and_rh(
    zone: ChartZone, pressure: float, *, step_temp: float
) -> PsychroCurve:
    assert zone.zone_type == "dbt-rh"
    # points for zone between constant dry bulb temps and RH
    t_min = zone.points_x[0]
    t_max = zone.points_x[-1]
    rh_min = zone.points_y[0]
    rh_max = zone.points_y[-1]
    assert rh_min >= 0.0 and rh_max <= 100.0
    assert t_min < t_max

    temps = np.arange(t_min, t_max + step_temp, step_temp)
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
        style=zone.style,
        type_curve=zone.zone_type,
        label=zone.label,
        internal_value=random_internal_value() if zone.label is None else None,
        annotation_style=zone.annotation_style,
    )


def _make_zone_delimited_by_volume_and_rh(
    zone: ChartZone,
    pressure: float,
    *,
    step_temp: float,
    dbt_min: float,
    dbt_max: float,
    w_min: float,
    w_max: float,
) -> PsychroCurve | None:
    assert zone.zone_type == "volume-rh"
    v_min, v_max = zone.points_x
    rh_min, rh_max = zone.points_y
    dbt_min_use = _adjust_temp_range_for_volume(
        (v_min, v_max), (dbt_min, dbt_max), pressure, step_temp
    )
    v_lines = make_constant_specific_volume_lines(
        w_min,
        pressure,
        np.array([v_min, v_max]),
        saturation_curve=make_saturation_line(
            dbt_min_use, dbt_max, step_temp, pressure
        ),
        style=CurveStyle(),
    )
    if not _valid_zone_delimiter_on_plot_limits(
        zone, v_lines, dbt_min, dbt_max, w_min, w_max
    ):
        return None

    rh_lines = make_constant_relative_humidity_lines(
        dbt_min_use,
        dbt_max,
        step_temp,
        pressure,
        [int(rh_min), int(rh_max)],
        style=CurveStyle(),
    )

    def _points_to_volume(dbt_values, w_values):
        return f_vec_moist_air_volume(dbt_values, w_values, pressure)

    return _zone_between_rh_and_rects(
        zone,
        rect_lines=v_lines,
        rh_lines=rh_lines,
        func_dbt_w_to_target=_points_to_volume,
    )


def _make_zone_delimited_by_dbt_and_wmax(
    zone: ChartZone,
    pressure: float,
    *,
    step_temp: float,
    dbt_min: float,
    dbt_max: float,
    w_min: float,
    w_max: float,
) -> PsychroCurve | None:
    assert zone.zone_type == "dbt-wmax"
    dbt_1, dbt_2 = zone.points_x
    w_1, w_2 = zone.points_y

    if dbt_1 > dbt_max or dbt_2 < dbt_min or w_1 > w_max or w_2 < w_min:
        # zone outside limits
        return None

    w_1 = max(w_1, w_min)
    w_2 = min(w_2, w_max)
    dbt_1 = max(dbt_1, dbt_min)
    dbt_2 = min(dbt_2, dbt_max)

    saturation = make_saturation_line(dbt_1, dbt_2, step_temp, pressure)
    if saturation.outside_limits(dbt_min, dbt_max, w_min, w_max):
        # just make a rectangle
        return PsychroCurve(
            x_data=np.array([dbt_1, dbt_2]),
            y_data=np.array([w_1, w_2]),
            style=zone.style,
            type_curve=zone.zone_type,
            label=zone.label,
            internal_value=w_2,
            annotation_style=zone.annotation_style,
        )

    # build path clockwise starting in left bottom corner
    path_x, path_y = [], []
    if saturation.y_data[0] < w_1:  # saturation cuts lower w value
        idx_start = (saturation.y_data > w_1).argmax()
        t_start, t_end = (
            saturation.x_data[idx_start - 1],
            saturation.x_data[idx_start],
        )
        w_start, w_end = (
            saturation.y_data[idx_start - 1],
            saturation.y_data[idx_start],
        )
        t_cut1, _w_cut1 = _crossing_point_between_rect_lines(
            segment_1_x=(dbt_1, dbt_2),
            segment_1_y=(w_1, w_1),
            segment_2_x=(t_start, t_end),
            segment_2_y=(w_start, w_end),
        )
        path_x.append(t_cut1)
        path_y.append(w_1)
    else:  # saturation cuts left y-axis
        idx_start = 0
        t_cut1, w_cut1 = saturation.x_data[0], saturation.y_data[0]

        path_x.append(dbt_1)
        path_y.append(w_1)
        path_x.append(t_cut1)
        path_y.append(w_cut1)

    if saturation.y_data[-1] < w_2:  # saturation cuts right dbt_2
        path_x += saturation.x_data[idx_start:].tolist()
        path_y += saturation.y_data[idx_start:].tolist()

        t_cut2, w_cut2 = saturation.x_data[-1], saturation.y_data[-1]
        path_x.append(t_cut2)
        path_y.append(w_cut2)
    else:  # saturation cuts top w_2
        idx_end = (saturation.y_data < w_2).argmin()
        path_x += saturation.x_data[idx_start:idx_end].tolist()
        path_y += saturation.y_data[idx_start:idx_end].tolist()

        t_start, t_end = (
            saturation.x_data[idx_end - 1],
            saturation.x_data[idx_end],
        )
        w_start, w_end = (
            saturation.y_data[idx_end - 1],
            saturation.y_data[idx_end],
        )
        t_cut2, _w_cut2 = _crossing_point_between_rect_lines(
            segment_1_x=(dbt_1, dbt_2),
            segment_1_y=(w_2, w_2),
            segment_2_x=(t_start, t_end),
            segment_2_y=(w_start, w_end),
        )
        path_x.append(t_cut2)
        path_y.append(w_2)

        path_x.append(dbt_2)
        path_y.append(w_2)

    path_x.append(dbt_2)
    path_y.append(w_1)

    # repeat 1st point to close path
    path_x.append(path_x[0])
    path_y.append(path_y[0])

    return PsychroCurve(
        x_data=np.array(path_x),
        y_data=np.array(path_y),
        style=zone.style,
        type_curve=zone.zone_type,
        label=zone.label,
        internal_value=w_2,
        annotation_style=zone.annotation_style,
    )


def make_zone_curve(
    zone_conf: ChartZone,
    *,
    pressure: float,
    step_temp: float,
    dbt_min: float,
    dbt_max: float,
    w_min: float,
    w_max: float,
) -> PsychroCurve | None:
    """Generate plot-points for zone definition."""
    if zone_conf.zone_type == "dbt-rh":
        # points for zone between vertical dbt lines and RH ranges
        return _make_zone_delimited_by_vertical_dbt_and_rh(
            zone_conf, pressure, step_temp=step_temp
        )

    if zone_conf.zone_type == "volume-rh":
        # points for zone between constant volume and RH ranges
        return _make_zone_delimited_by_volume_and_rh(
            zone_conf,
            pressure,
            step_temp=step_temp,
            dbt_min=dbt_min,
            dbt_max=dbt_max,
            w_min=w_min,
            w_max=w_max,
        )
    if zone_conf.zone_type == "enthalpy-rh":
        # points for zone between constant enthalpy and RH ranges
        return _make_zone_delimited_by_enthalpy_and_rh(
            zone_conf,
            pressure,
            step_temp=step_temp,
            dbt_min=dbt_min,
            dbt_max=dbt_max,
            w_min=w_min,
            w_max=w_max,
        )

    if zone_conf.zone_type == "dbt-wmax":
        # points for zone between abs humid and dbt ranges
        return _make_zone_delimited_by_dbt_and_wmax(
            zone_conf,
            pressure,
            step_temp=step_temp,
            dbt_min=dbt_min,
            dbt_max=dbt_max,
            w_min=w_min,
            w_max=w_max,
        )

    # expect points in plot coordinates!
    assert zone_conf.zone_type == "xy-points"
    zone_value = random_internal_value() if zone_conf.label is None else None
    return PsychroCurve(
        x_data=np.array(zone_conf.points_x),
        y_data=np.array(zone_conf.points_y),
        style=zone_conf.style,
        type_curve=zone_conf.zone_type,
        label=zone_conf.label,
        internal_value=zone_value,
    )


def make_over_saturated_zone(
    saturation: PsychroCurve,
    *,
    dbt_min: float,
    dbt_max: float,
    w_min: float,
    w_max: float,
    color_fill: str | list[float] = "#0C92F6FF",
) -> PsychroCurve | None:
    """Generate plot-points for a Patch in the over-saturated zone of chart."""
    if saturation.outside_limits(dbt_min, dbt_max, w_min, w_max):
        return None

    path_x, path_y = [], []
    if saturation.y_data[0] < w_min:  # saturation cuts bottom x-axis
        idx_start = (saturation.y_data > w_min).argmax()
        t_start, t_end = (
            saturation.x_data[idx_start - 1],
            saturation.x_data[idx_start],
        )
        w_start, w_end = (
            saturation.y_data[idx_start - 1],
            saturation.y_data[idx_start],
        )
        t_cut1, _w_cut1 = _crossing_point_between_rect_lines(
            segment_1_x=(dbt_min, dbt_max),
            segment_1_y=(w_min, w_min),
            segment_2_x=(t_start, t_end),
            segment_2_y=(w_start, w_end),
        )
        path_x.append(t_cut1)
        path_y.append(w_min)

        path_x.append(dbt_min)
        path_y.append(w_min)
    else:  # saturation cuts left y-axis
        idx_start = 0
        t_cut1, w_cut1 = saturation.x_data[0], saturation.y_data[0]

        path_x.append(t_cut1)
        path_y.append(w_cut1)

    # top left corner
    path_x.append(dbt_min)
    path_y.append(w_max)

    if saturation.y_data[-1] < w_max:  # saturation cuts right y-axis
        # top right corner
        path_x.append(dbt_max)
        path_y.append(w_max)
        t_cut2, w_cut2 = saturation.x_data[-1], saturation.y_data[-1]
        path_x.append(t_cut2)
        path_y.append(w_cut2)

        path_x += saturation.x_data[idx_start:].tolist()[::-1]
        path_y += saturation.y_data[idx_start:].tolist()[::-1]
    else:  # saturation cuts top x-axis
        idx_end = (saturation.y_data < w_max).argmin()
        t_start, t_end = (
            saturation.x_data[idx_end - 1],
            saturation.x_data[idx_end],
        )
        w_start, w_end = (
            saturation.y_data[idx_end - 1],
            saturation.y_data[idx_end],
        )
        t_cut2, _w_cut2 = _crossing_point_between_rect_lines(
            segment_1_x=(dbt_min, dbt_max),
            segment_1_y=(w_max, w_max),
            segment_2_x=(t_start, t_end),
            segment_2_y=(w_start, w_end),
        )
        path_x.append(t_cut2)
        path_y.append(w_max)

        path_x += saturation.x_data[idx_start:idx_end].tolist()[::-1]
        path_y += saturation.y_data[idx_start:idx_end].tolist()[::-1]

    return PsychroCurve(
        x_data=np.array(path_x),
        y_data=np.array(path_y),
        style=ZoneStyle.model_validate(
            {
                "edgecolor": [0, 0, 0, 0],
                "facecolor": color_fill,
                "linewidth": 0,
                "linestyle": "none",
            }
        ),
        type_curve="over_saturated",
        internal_value=0,
    )
