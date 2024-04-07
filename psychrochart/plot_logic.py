"""A library to make psychrometric charts and overlay information in them."""

import logging
from math import atan2, degrees
from typing import Any, AnyStr

import numpy as np
from matplotlib import patches
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.path import Path
from matplotlib.text import Annotation
from scipy.spatial import ConvexHull, QhullError

from psychrochart.chart_entities import (
    ChartRegistry,
    make_item_gid,
    reg_artist,
)
from psychrochart.models.annots import ChartAnnots
from psychrochart.models.config import ChartConfig
from psychrochart.models.curves import (
    PsychroChartModel,
    PsychroCurve,
    PsychroCurves,
)
from psychrochart.models.styles import CurveStyle, ZoneStyle
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
        tilt_curve = 1e12 if delta_x == 0 else delta_y / delta_x
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

    text_style["color"] = (
        mod_color(curve.style.color, -25)
        if isinstance(curve.style, CurveStyle)
        else mod_color(curve.style.edgecolor, -25)
    )
    if ha is not None:
        text_style["ha"] = ha
    if va is not None:
        text_style["va"] = va

    if curve.annotation_style is not None:
        text_style.update(curve.annotation_style.export_style())
    text_style.update(**params)

    return _annotate_label(ax, label, text_x, text_y, rotation, text_style)


def plot_curve(
    curve: PsychroCurve, ax: Axes, label_prefix: str | None = None
) -> dict[str, Artist]:
    """Plot the curve, if it's between chart limits."""
    artists: dict[str, Artist] = {}
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    if curve.outside_limits(xmin, xmax, ymin, ymax):
        logging.info(
            "%s (name:%s) not between limits ([%.2g, %.2g, %.2g, %.2g]) "
            "-> x:%s, y:%s",
            curve.type_curve,
            curve.label or str(curve.internal_value),
            xmin,
            xmax,
            ymin,
            ymax,
            curve.x_data,
            curve.y_data,
        )
        return {}

    if isinstance(curve.style, ZoneStyle):
        if len(curve.y_data) == 2:  # draw a rectangle!
            patch = patches.Rectangle(
                (curve.x_data[0], curve.y_data[0]),
                width=curve.x_data[1] - curve.x_data[0],
                height=curve.y_data[1] - curve.y_data[0],
                **curve.style.model_dump(),
            )
            bbox_p = patch.get_extents()
        else:
            assert len(curve.y_data) > 2
            verts = list(zip(curve.x_data, curve.y_data))
            codes = (
                [Path.MOVETO]
                + [Path.LINETO] * (len(curve.y_data) - 2)
                + [Path.CLOSEPOLY]
            )
            path = Path(verts, codes)
            patch = patches.PathPatch(path, **curve.style.model_dump())
            bbox_p = path.get_extents()
        ax.add_patch(patch)
        gid_zone = make_item_gid(
            "zone",
            family_label=label_prefix or curve.type_curve,
            name=curve.curve_id,
        )
        reg_artist(
            gid_zone,
            patch,
            artists,
        )
        if curve.label is not None:
            text_x = 0.5 * (bbox_p.x0 + bbox_p.x1)
            text_y = 0.5 * (bbox_p.y0 + bbox_p.y1)
            style_params = {
                "ha": "center",
                "va": "center",
                "backgroundcolor": [1, 1, 1, 0.4],
            }

            assert isinstance(curve.style, ZoneStyle)
            if curve.annotation_style is not None:
                style_params.update(curve.annotation_style.export_style())
            reg_artist(
                "label_" + gid_zone,
                _annotate_label(
                    ax, curve.label, text_x, text_y, 0, style_params
                ),
                artists,
            )
    else:
        [artist_line] = ax.plot(
            curve.x_data, curve.y_data, **curve.style.model_dump()
        )
        kind = (
            (label_prefix or curve.type_curve)
            if len(curve.x_data) > 1
            else "point"
        )
        gid_line = make_item_gid(kind or "unknown", name=curve.curve_id)
        reg_artist(gid_line, artist_line, artists)
        if curve.label is not None:
            reg_artist(
                "label_" + gid_line, add_label_to_curve(curve, ax), artists
            )

    return artists


def plot_curves_family(
    family: PsychroCurves | None, ax: Axes
) -> dict[str, Artist]:
    """Plot all curves in the family."""
    if family is None:
        return {}
    artists: dict[str, Artist] = {
        gid: item
        for curve in family.curves
        for gid, item in plot_curve(
            curve, ax, label_prefix=family.family_label
        ).items()
    }
    # Curves family labelling
    if family.curves and family.family_label is not None:
        # artist for legend (1 label for each family)
        min_params = {"marker": "D", "markersize": 10}
        [artist_fam_label] = ax.plot(
            [-1],
            [-1],
            label=family.family_label,
            **(min_params | family.curves[0].style.model_dump()),
        )
        gid_family_label = make_item_gid(
            "label_legend", name=family.family_label
        )
        artist_fam_label.set_gid(gid_family_label)
        artists[gid_family_label] = artist_fam_label

    return artists


def _apply_spines_style(axes, style, location="right") -> None:
    for key in style:
        try:
            getattr(axes.spines[location], f"set_{key}")(style[key])
        except Exception as exc:  # noqa: BLE001, pragma: no cover
            logging.error(
                f"Error trying to apply spines attrs: {exc}. "
                f"({dir(axes.spines[location])})"
            )


def apply_axis_styling(config: ChartConfig, ax: Axes) -> dict[str, Artist]:  # noqa: C901
    """Setup matplotlib Axes object for the chart."""
    layout_artists: dict[str, Artist] = {}
    reg_artist("chart_x_axis", ax.xaxis, layout_artists)
    reg_artist("chart_y_axis", ax.yaxis, layout_artists)
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
    ax.set_xlim(config.dbt_min, config.dbt_max)
    ax.set_ylim(config.w_min, config.w_max)
    ax.grid(False, which="both")
    # Apply axis styles
    if config.figure.x_label is not None:
        style_axis = config.figure.x_axis_labels.model_dump()
        style_axis["fontsize"] *= 1.2
        artist_xlabel = ax.set_xlabel(config.figure.x_label, **style_axis)
        reg_artist("chart_x_axis_label", artist_xlabel, layout_artists)
    if config.figure.y_label is not None:
        style_axis = config.figure.y_axis_labels.model_dump()
        style_axis["fontsize"] *= 1.2
        artist_ylabel = ax.set_ylabel(config.figure.y_label, **style_axis)
        reg_artist("chart_y_axis_label", artist_ylabel, layout_artists)
    if config.figure.title is not None:
        artist_title = ax.set_title(
            config.figure.title,
            fontsize=config.figure.fontsize * 1.5,
            fontweight="bold",
        )
        reg_artist("chart_title", artist_title, layout_artists)

    _apply_spines_style(
        ax, config.figure.y_axis.model_dump(), location="right"
    )
    _apply_spines_style(
        ax, config.figure.x_axis.model_dump(), location="bottom"
    )
    reg_artist("chart_x_axis_bottom_line", ax.spines["bottom"], layout_artists)
    reg_artist("chart_y_axis_right_line", ax.spines["right"], layout_artists)
    if config.figure.partial_axis:  # Hide left and top axis
        ax.spines["left"].set_visible(False)
        ax.spines["top"].set_visible(False)
    else:
        _apply_spines_style(
            ax, config.figure.y_axis.model_dump(), location="left"
        )
        _apply_spines_style(
            ax, config.figure.x_axis.model_dump(), location="top"
        )
        reg_artist("chart_x_axis_top_line", ax.spines["top"], layout_artists)
        reg_artist("chart_y_axis_left_line", ax.spines["left"], layout_artists)
    if config.figure.x_axis_ticks is not None:
        ax.tick_params(axis="x", **config.figure.x_axis_ticks.model_dump())
    if config.figure.y_axis_ticks is not None:
        ax.tick_params(axis="y", **config.figure.y_axis_ticks.model_dump())

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
                [f"{t:g}" for t in ticks],
                **config.figure.x_axis_labels.model_dump(),
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
                [f"{t:g}" for t in ticks],
                **config.figure.y_axis_labels.model_dump(),
            )
    else:
        ax.set_yticks([])
    return layout_artists


def plot_chart(
    chart: PsychroChartModel, ax: Axes, registry: ChartRegistry | None = None
) -> ChartRegistry:
    """Plot the psychrochart curves on given Axes."""
    if registry is None:
        registry = ChartRegistry()
    # Plot curves:
    if data := plot_curves_family(chart.constant_dry_temp_data, ax):
        registry.constant_dry_temp = data
    if data := plot_curves_family(chart.constant_humidity_data, ax):
        registry.constant_humidity = data
    if data := plot_curves_family(chart.constant_h_data, ax):
        registry.constant_h = data
    if data := plot_curves_family(chart.constant_v_data, ax):
        registry.constant_v = data
    if data := plot_curves_family(chart.constant_rh_data, ax):
        registry.constant_rh = data
    if data := plot_curves_family(chart.constant_wbt_data, ax):
        registry.constant_wbt = data
    registry.saturation = plot_curve(chart.saturation, ax)

    # Plot zones:
    for zone in chart.zones:
        registry.zones.update(plot_curve(zone, ax))
    return registry


def plot_annots_dbt_rh(ax: Axes, annots: ChartAnnots) -> dict[str, Artist]:
    """Plot chat annotations in given matplotlib Axes, return `Artist` objs."""
    annot_artists: dict[str, Artist] = {}
    for d_con in annots.connectors:
        x_start, y_start = annots.get_point_by_name(d_con.start)
        x_end, y_end = annots.get_point_by_name(d_con.end)
        x_line = [x_start, x_end]
        y_line = [y_start, y_end]
        d_con_gid = make_item_gid(
            "connector", name=d_con.label or f"{d_con.start}_{d_con.end}"
        )
        [artist_connector] = ax.plot(
            x_line,
            y_line,
            label=d_con.label,
            dash_capstyle="round",
            **d_con.style.model_dump(),
        )
        reg_artist(d_con_gid, artist_connector, annot_artists)
        if d_con.outline_marker_width:
            [artist_connector_marker] = ax.plot(
                x_line,
                y_line,
                color=[*d_con.style.color[:3], 0.15],
                lw=d_con.outline_marker_width,
                solid_capstyle="round",
            )
            reg_artist(
                d_con_gid + "_outline_mark",
                artist_connector_marker,
                annot_artists,
            )

    forbidden = set()
    if annots.use_scatter:
        f_plot = ax.scatter
        forbidden.add("markersize")
    else:
        f_plot = ax.plot
    for name, series in annots.series.items():
        style = {k: v for k, v in series.style.items() if k not in forbidden}
        artists = f_plot(
            series.x_data, series.y_data, label=series.label, **style
        )
        artist_line = artists[0] if isinstance(artists, list) else artists
        line_gid = make_item_gid("series", name=series.label or name)
        reg_artist(line_gid, artist_line, annot_artists)

    for name, point in annots.points.items():
        style = {k: v for k, v in point.style.items() if k not in forbidden}
        artists = f_plot(point.xy[0], point.xy[1], label=point.label, **style)
        artist_point = artists[0] if isinstance(artists, list) else artists
        line_gid = make_item_gid("point", name=point.label or name)
        reg_artist(line_gid, artist_point, annot_artists)

    if ConvexHull is None or not annots.areas:
        return annot_artists

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

        area_gid = make_item_gid(
            "convexhull", name=",".join(convex_area.point_names)
        )
        for i, simplex in enumerate(hull.simplices):
            [artist_contour] = ax.plot(
                int_points[simplex, 0],
                int_points[simplex, 1],
                **convex_area.line_style,
            )
            reg_artist(area_gid + f"_s{i+1}", artist_contour, annot_artists)
        [artist_area] = ax.fill(
            int_points[hull.vertices, 0],
            int_points[hull.vertices, 1],
            **convex_area.fill_style,
        )
        reg_artist(area_gid, artist_area, annot_artists)

    return annot_artists
