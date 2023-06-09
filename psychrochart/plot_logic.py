"""A library to make psychrometric charts and overlay information in them."""
import logging
from math import atan2, degrees
from typing import Any, AnyStr

from matplotlib import patches
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.path import Path
from matplotlib.text import Annotation
import numpy as np
from scipy.spatial import ConvexHull, QhullError

from psychrochart.models.annots import ChartAnnots
from psychrochart.models.config import ChartConfig
from psychrochart.models.curves import (
    PsychroChartModel,
    PsychroCurve,
    PsychroCurves,
)
from psychrochart.models.styles import ZoneStyle
from psychrochart.util import mod_color


def _annotate_label(
    ax: Axes,
    label: AnyStr,
    text_x: float,
    text_y: float,
    rotation: float,
    text_style: dict[str, Any],
) -> Annotation:
    if abs(rotation) > 0:
        text_loc = np.array((text_x, text_y))
        text_style["rotation"] = ax.transData.transform_angles(
            np.array((rotation,)), text_loc.reshape((1, 2))
        )[0]
        text_style["rotation_mode"] = "anchor"
    return ax.annotate(label, (text_x, text_y), **text_style)


def add_label_to_curve(
    curve: PsychroCurve,
    ax: Axes,
    text_label: str | None = None,
    va: str | None = None,
    ha: str | None = None,
    loc: float | None = None,
    **params,
) -> Annotation:
    """Annotate the curve with its label."""
    num_samples = len(curve.x_data)
    assert num_samples > 1
    text_style = {"va": "bottom", "ha": "left", "color": [0.0, 0.0, 0.0]}
    loc_f: float = curve.label_loc if loc is None else loc
    label: str = (
        (curve.label if curve.label is not None else "")
        if text_label is None
        else text_label
    )

    def _tilt_params(x_data, y_data, idx_0, idx_f):
        delta_x = x_data[idx_f] - curve.x_data[idx_0]
        delta_y = y_data[idx_f] - curve.y_data[idx_0]
        rotation_deg = degrees(atan2(delta_y, delta_x))
        if delta_x == 0:
            tilt_curve = 1e12
        else:
            tilt_curve = delta_y / delta_x
        return rotation_deg, tilt_curve

    if num_samples == 2:
        xmin, xmax = ax.get_xlim()
        rotation, tilt = _tilt_params(curve.x_data, curve.y_data, 0, 1)
        if abs(rotation) == 90:
            text_x = curve.x_data[0]
            text_y = curve.y_data[0] + loc_f * (
                curve.y_data[1] - curve.y_data[0]
            )
        elif loc_f == 1.0:
            if curve.x_data[1] > xmax:
                text_x = xmax
                text_y = curve.y_data[0] + tilt * (xmax - curve.x_data[0])
            else:
                text_x, text_y = curve.x_data[1], curve.y_data[1]
            label += "    "
            text_style["ha"] = "right"
        else:
            text_x = curve.x_data[0] + loc_f * (xmax - xmin)
            if text_x < xmin:
                text_x = xmin + loc_f * (xmax - xmin)
            text_y = curve.y_data[0] + tilt * (text_x - curve.x_data[0])
    else:
        idx = min(num_samples - 2, int(num_samples * loc_f))
        rotation, tilt = _tilt_params(curve.x_data, curve.y_data, idx, idx + 1)
        text_x, text_y = curve.x_data[idx], curve.y_data[idx]
        text_style["ha"] = "center"

    text_style["color"] = mod_color(curve.style.color, -25)
    if ha is not None:
        text_style["ha"] = ha
    if va is not None:
        text_style["va"] = va
    if params:
        text_style.update(params)

    return _annotate_label(ax, label, text_x, text_y, rotation, text_style)


def plot_curve(
    curve: PsychroCurve, ax: Axes, label_prefix: str | None = None
) -> list[Artist]:
    """Plot the curve, if it's between chart limits."""
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    if (
        curve.x_data is None
        or curve.y_data is None
        or max(curve.y_data) < ymin
        or max(curve.x_data) < xmin
        or min(curve.y_data) > ymax
        or min(curve.x_data) > xmax
    ):
        logging.info(
            "%s (label:%s) not between limits ([%.2g, %.2g, %.2g, %.2g]) "
            "-> x:%s, y:%s",
            curve.type_curve,
            curve.label or "unnamed",
            xmin,
            xmax,
            ymin,
            ymax,
            curve.x_data,
            curve.y_data,
        )
        return []

    artists = []
    if isinstance(curve.style, ZoneStyle):
        assert len(curve.y_data) > 2
        verts = list(zip(curve.x_data, curve.y_data))
        codes = (
            [Path.MOVETO]
            + [Path.LINETO] * (len(curve.y_data) - 2)
            + [Path.CLOSEPOLY]
        )
        path = Path(verts, codes)
        patch = patches.PathPatch(path, **curve.style.dict())
        ax.add_patch(patch)
        artists.append(patch)

        if curve.label is not None:
            bbox_p = path.get_extents()
            text_x = 0.5 * (bbox_p.x0 + bbox_p.x1)
            text_y = 0.5 * (bbox_p.y0 + bbox_p.y1)
            style_params = {
                "ha": "center",
                "va": "center",
                "backgroundcolor": [1, 1, 1, 0.4],
            }
            assert isinstance(curve.style, ZoneStyle)
            style_params["color"] = mod_color(curve.style.edgecolor, -25)
            artist_label = _annotate_label(
                ax, curve.label, text_x, text_y, 0, style_params
            )
            artists.append(artist_label)
    else:
        artist_line = ax.plot(curve.x_data, curve.y_data, **curve.style.dict())
        artists.append(artist_line)
        if curve.label is not None:
            artists.append(add_label_to_curve(curve, ax))

    return artists


def plot_curves_family(family: PsychroCurves | None, ax: Axes) -> list[Artist]:
    """Plot all curves in the family."""
    artists: list[Artist] = []
    if family is None:
        return artists

    [
        plot_curve(curve, ax, label_prefix=family.family_label)
        for curve in family.curves
    ]
    # Curves family labelling
    if family.curves and family.family_label is not None:
        artist_fam_label = ax.plot(
            [-1],
            [-1],
            label=family.family_label,
            marker="D",
            markersize=10,
            **family.curves[0].style.dict(),
        )
        artists.append(artist_fam_label)

    # return [
    #     art for art in artist_curves + artist_labels if art is not None
    # ]
    # TODO collect artists from plot_curve
    return []


def _apply_spines_style(axes, style, location="right") -> None:
    for key in style:
        try:
            getattr(axes.spines[location], f"set_{key}")(style[key])
        except Exception as exc:  # pragma: no cover
            logging.error(
                f"Error trying to apply spines attrs: {exc}. "
                f"({dir(axes.spines[location])})"
            )


def apply_axis_styling(config: ChartConfig, ax: Axes) -> None:
    """Setup matplotlib Axes object for the chart."""
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
    ax.set_xlim(config.dbt_min, config.dbt_max)
    ax.set_ylim(config.w_min, config.w_max)
    ax.grid(False, which="both")
    # Apply axis styles
    if config.figure.x_label is not None:
        style_axis = config.figure.x_axis_labels.dict()
        style_axis["fontsize"] *= 1.2
        ax.set_xlabel(config.figure.x_label, **style_axis)
    if config.figure.y_label is not None:
        style_axis = config.figure.y_axis_labels.dict()
        style_axis["fontsize"] *= 1.2
        ax.set_ylabel(config.figure.y_label, **style_axis)
    if config.figure.title is not None:
        ax.set_title(
            config.figure.title,
            fontsize=config.figure.fontsize * 1.5,
            fontweight="bold",
        )

    _apply_spines_style(ax, config.figure.y_axis.dict(), location="right")
    _apply_spines_style(ax, config.figure.x_axis.dict(), location="bottom")
    if config.figure.partial_axis:  # Hide left and top axis
        ax.spines["left"].set_visible(False)
        ax.spines["top"].set_visible(False)
    else:
        _apply_spines_style(ax, config.figure.y_axis.dict(), location="left")
        _apply_spines_style(ax, config.figure.x_axis.dict(), location="top")

    if config.figure.x_axis_ticks is not None:
        ax.tick_params(axis="x", **config.figure.x_axis_ticks.dict())
    if config.figure.y_axis_ticks is not None:
        ax.tick_params(axis="y", **config.figure.y_axis_ticks.dict())

    # set tick labels in main axes
    if config.chart_params.with_constant_dry_temp:
        step_label = config.chart_params.constant_temp_label_step
        if step_label > 0:  # Explicit xticks
            ticks = np.arange(
                config.dbt_min, config.dbt_max + step_label / 10, step_label
            )
            if not config.chart_params.constant_temp_label_include_limits:
                ticks = [
                    t
                    for t in ticks
                    if t not in [config.dbt_min, config.dbt_max]
                ]
            ax.set_xticks(ticks)
            ax.set_xticklabels(
                [f"{t:g}" for t in ticks], **config.figure.x_axis_labels.dict()
            )
    else:
        ax.set_xticks([])

    if config.chart_params.with_constant_humidity:
        step_label = config.chart_params.constant_humid_label_step
        if step_label > 0:  # Explicit xticks
            ticks = np.arange(
                config.w_min, config.w_max + step_label / 10, step_label
            )
            if not config.chart_params.constant_humid_label_include_limits:
                ticks = [
                    t for t in ticks if t not in [config.w_min, config.w_max]
                ]
            ax.set_yticks(ticks)
            ax.set_yticklabels(
                [f"{t:g}" for t in ticks], **config.figure.y_axis_labels.dict()
            )
    else:
        ax.set_yticks([])


def plot_chart(chart: PsychroChartModel, ax: Axes) -> Axes:
    """Plot the psychrochart curves on given Axes."""
    # Plot curves:
    plot_curves_family(chart.constant_dry_temp_data, ax)
    plot_curves_family(chart.constant_humidity_data, ax)
    plot_curves_family(chart.constant_h_data, ax)
    plot_curves_family(chart.constant_v_data, ax)
    plot_curves_family(chart.constant_rh_data, ax)
    plot_curves_family(chart.constant_wbt_data, ax)
    plot_curves_family(chart.saturation, ax)

    # Plot zones:
    for zone in chart.zones:
        plot_curves_family(zone, ax)
    return ax


def plot_annots_dbt_rh(
    ax: Axes, annots: ChartAnnots
) -> list[Artist | list[Artist]]:
    """Plot chat annotations in given matplotlib Axes, return `Artist` objs."""
    _handlers_annotations = []
    for d_con in annots.connectors:
        x_start, y_start = annots.get_point_by_name(d_con.start)
        x_end, y_end = annots.get_point_by_name(d_con.end)
        x_line = [x_start, x_end]
        y_line = [y_start, y_end]
        _handlers_annotations.append(
            ax.plot(
                x_line,
                y_line,
                label=d_con.label,
                dash_capstyle="round",
                **d_con.style.dict(),
            )
        )
        if d_con.outline_marker_width:
            _handlers_annotations.append(
                ax.plot(
                    x_line,
                    y_line,
                    color=[*d_con.style.color[:3], 0.15],
                    lw=d_con.outline_marker_width,
                    solid_capstyle="round",
                )
            )

    forbidden = set()
    if annots.use_scatter:
        f_plot = ax.scatter
        forbidden.add("markersize")
    else:
        f_plot = ax.plot
    for series in annots.series.values():
        style = {k: v for k, v in series.style.items() if k not in forbidden}
        _handlers_annotations.append(
            f_plot(series.x_data, series.y_data, label=series.label, **style)
        )

    for point in annots.points.values():
        style = {k: v for k, v in point.style.items() if k not in forbidden}
        _handlers_annotations.append(
            f_plot(point.xy[0], point.xy[1], label=point.label, **style)
        )

    if ConvexHull is None or not annots.areas:
        return _handlers_annotations

    for convex_area in annots.areas:
        int_points = np.array(
            [annots.get_point_by_name(key) for key in convex_area.point_names]
        )
        try:
            assert len(int_points) >= 3
            hull = ConvexHull(int_points)
        except (AssertionError, QhullError):  # pragma: no cover
            logging.error(f"QhullError with points: {int_points}")
            continue

        for simplex in hull.simplices:
            _handlers_annotations.append(
                ax.plot(
                    int_points[simplex, 0],
                    int_points[simplex, 1],
                    **convex_area.line_style,
                )
            )
        _handlers_annotations.append(
            ax.fill(
                int_points[hull.vertices, 0],
                int_points[hull.vertices, 1],
                **convex_area.fill_style,
            )
        )

    return _handlers_annotations
