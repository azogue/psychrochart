"""Tests plotting."""

from psychrochart.agg import PsychroChart
from tests.conftest import TEST_BASEDIR, timeit


@timeit("make_chart")
def _make_chart(path_save=None):
    chart = PsychroChart.create("minimal")
    # Zones:
    zones_conf = {
        "zones": [
            {
                "zone_type": "dbt-rh",
                "style": {
                    "edgecolor": [1.0, 0.749, 0.0, 0.8],
                    "facecolor": [1.0, 0.749, 0.0, 0.2],
                    "linewidth": 2,
                    "linestyle": "--",
                },
                "points_x": [23, 28],
                "points_y": [40, 60],
                "label": "Summer",
            },
            {
                "zone_type": "dbt-rh",
                "style": {
                    "edgecolor": [0.498, 0.624, 0.8],
                    "facecolor": [0.498, 0.624, 1.0, 0.2],
                    "linewidth": 2,
                    "linestyle": "--",
                },
                "points_x": [18, 23],
                "points_y": [35, 55],
                "label": "Winter",
            },
        ]
    }
    chart.append_zones(zones_conf)
    # Plotting
    chart.plot()
    # Vertical lines
    t_min, t_opt, t_max = 16, 23, 30
    chart.plot_vertical_dry_bulb_temp_line(
        t_min,
        {"color": [0.0, 0.125, 0.376], "lw": 2, "ls": ":"},
        f"  TOO COLD ({t_min}°C)",
        ha="left",
        loc=0.0,
        fontsize=14,
    )
    chart.plot_vertical_dry_bulb_temp_line(
        t_opt, {"color": [0.475, 0.612, 0.075], "lw": 2, "ls": ":"}
    )
    chart.plot_vertical_dry_bulb_temp_line(
        t_max,
        {"color": [1.0, 0.0, 0.247], "lw": 2, "ls": ":"},
        f"TOO HOT ({t_max}°C)  ",
        ha="right",
        loc=1,
        reverse=True,
        fontsize=14,
    )
    # Save to disk the base chart
    if path_save is not None:
        path_svg = TEST_BASEDIR / path_save
        chart.save(path_svg)
    return chart


@timeit("add_points")
def _add_points(chart, with_connectors=True, path_save=None):
    if with_connectors:
        # Append points and connectors
        points = {
            "exterior": {
                "label": "Exterior",
                "style": {
                    "color": [0.855, 0.004, 0.278, 0.8],
                    "marker": "X",
                    "markersize": 15,
                },
                "xy": (31.06, 32.9),
            },
            "exterior_estimated": {
                "label": "Estimated (Weather service)",
                "style": {
                    "color": [0.573, 0.106, 0.318, 0.5],
                    "marker": "x",
                    "markersize": 10,
                },
                "xy": (36.7, 25.0),
            },
            "interior": {
                "label": "Interior",
                "style": {
                    "color": [0.592, 0.745, 0.051, 0.9],
                    "marker": "o",
                    "markersize": 30,
                },
                "xy": (29.42, 52.34),
            },
        }
        connectors = [
            {
                "start": "exterior",
                "end": "exterior_estimated",
                "style": {
                    "color": [0.573, 0.106, 0.318, 0.7],
                    "linewidth": 2,
                    "linestyle": "-.",
                },
            },
            {
                "start": "exterior",
                "end": "interior",
                "style": {
                    "color": [0.855, 0.145, 0.114, 0.8],
                    "linewidth": 2,
                    "linestyle": ":",
                },
            },
        ]

        convex_groups = [
            (
                ["exterior", "exterior_estimated", "interior"],
                {"color": "darkgreen", "lw": 2, "alpha": 0.5, "ls": ":"},
                {"color": "darkgreen", "lw": 0, "alpha": 0.3},
            ),
        ]
        chart.plot_points_dbt_rh(
            points, connectors, convex_groups=convex_groups
        )
    else:
        points = {
            "exterior": (31.06, 32.9),
            "exterior_estimated": (36.7, 25.0),
            "interior": (29.42, 52.34),
        }
        chart.plot_points_dbt_rh(points)
    # Save to disk
    if path_save is not None:
        path_svg = TEST_BASEDIR / path_save
        chart.save(path_svg)


@timeit("MAKE_CHARTS")
def _make_charts(with_reuse=False):
    name = "test_reuse_chart_" if with_reuse else "test_noreuse_chart_"
    chart = _make_chart()
    _add_points(chart, True, f"{name}_1.svg")

    if with_reuse:
        chart.remove_annotations()
    else:
        chart = _make_chart()
    _add_points(chart, False, f"{name}_2.svg")


def _draw_chart(path_img, chart=None):
    if chart is None:
        chart = _make_chart()
    chart.plot_legend()
    _add_points(chart, True, path_img)
    chart.close_fig()


def test_reuse_psychrochart():
    """Customize a chart with some additions"""
    _make_charts(with_reuse=True)


def test_no_reuse_psychrochart():
    """Customize a chart with some additions"""
    _make_charts(with_reuse=False)


def test_redraw_psychrochart():
    """Test the workflow to redraw a chart."""
    counter = 0
    chart = _make_chart()
    while counter < 10:
        _draw_chart("test_redraw_chart_1.svg", chart)
        counter += 1
