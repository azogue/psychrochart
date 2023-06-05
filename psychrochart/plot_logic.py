"""A library to make psychrometric charts and overlay information in them."""
import logging

from matplotlib.artist import Artist
from matplotlib.axes import Axes
import numpy as np
from scipy.spatial import ConvexHull, QhullError

from psychrochart.models.annots import ChartAnnots
from psychrochart.models.config import ChartConfig
from psychrochart.models.curves import PsychroChartModel


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
    ax.grid(False)
    ax.grid(False, which="minor")
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
    if chart.constant_dry_temp_data is not None:
        chart.constant_dry_temp_data.plot(ax)
    if chart.constant_humidity_data is not None:
        chart.constant_humidity_data.plot(ax)
    if chart.constant_h_data is not None:
        chart.constant_h_data.plot(ax)
    if chart.constant_v_data is not None:
        chart.constant_v_data.plot(ax)
    if chart.constant_rh_data is not None:
        chart.constant_rh_data.plot(ax)
    if chart.constant_wbt_data is not None:
        chart.constant_wbt_data.plot(ax)
    chart.saturation.plot(ax)

    # Plot zones:
    for zone in chart.zones:
        zone.plot(ax=ax)
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
        # TODO document fix for issue #14: removing marker by default
        if d_con.outline_marker_width:
            _handlers_annotations.append(
                ax.plot(
                    x_line,
                    y_line,
                    color=[*d_con.style.color[:3], 0.15],
                    lw=d_con.outline_marker_width,  # lw=50,
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
