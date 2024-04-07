"""Tests plotting."""

from typing import TYPE_CHECKING

import numpy as np
import pytest

from psychrochart import PsychroChart
from psychrochart.models.config import ChartZone
from psychrochart.models.parsers import load_config
from tests.conftest import store_test_chart, TEST_BASEDIR

if TYPE_CHECKING:
    from psychrochart.models.annots import ConvexGroupTuple


def test_chart_overlay_points_and_zones():
    """Customize a chart with some additions from a default style."""
    # 1x zone + 3 simple-points + convex-g
    # Load config
    config = load_config("minimal")

    # Customization
    config.limits.pressure_kpa = 90.5
    config.figure.x_label = None
    config.figure.y_label = None
    config.saturation.linewidth = 3
    config.chart_params.with_constant_dry_temp = False
    config.chart_params.with_constant_humidity = False
    config.chart_params.with_constant_wet_temp = False
    config.chart_params.with_constant_h = False

    # Chart creation
    chart = PsychroChart.create(config)
    assert chart.pressure == 90500.0

    # bad zone definition
    with pytest.raises(ValueError):
        ChartZone.model_validate(
            {"zone_type": "not_recognized_type", "label": "Bad zone"}
        )

    # Zones:
    zones_conf = {
        "zones": [
            {
                "zone_type": "xy-points",
                "style": {
                    "linewidth": 2,
                    "linestyle": "--",
                    "edgecolor": [0.498, 0.624, 0.8],
                    "facecolor": [0.498, 0.624, 1.0, 0.3],
                },
                "points_x": [23, 28, 28, 24, 23],
                "points_y": [1, 3, 4, 4, 2],
                "label": "Custom",
            },
            # {"zone_type": "not_recognized_type", "label": "Bad zone"},
        ]
    }
    chart.append_zones(zones_conf)

    # Plotting
    chart.plot()

    points = {
        "exterior": (31.06, 32.9),
        "exterior_estimated": (36.7, 25.0),
        "interior": (29.42, 52.34),
    }

    convex_groups: list[ConvexGroupTuple] = [
        (["exterior", "exterior_estimated", "interior"], {}, {}),
    ]
    chart.plot_points_dbt_rh(points, convex_groups=convex_groups)

    # Legend
    chart.plot_legend(markerscale=1.0, fontsize=11, labelspacing=1.3)

    # Save to disk
    store_test_chart(chart, "chart_overlay_test.svg")


def test_chart_overlay_minimal():
    # Creation from preset + customization
    chart = PsychroChart.create("minimal")
    chart.config.limits.pressure_kpa = 100.5
    chart.config.figure.x_label = None
    chart.config.figure.x_axis_ticks = None
    chart.config.figure.y_label = None
    chart.config.figure.y_axis_ticks = None
    chart.config.saturation.linewidth = 3
    chart.config.chart_params.constant_temp_label_step = -1
    chart.config.chart_params.constant_humid_label_step = -1
    chart.config.chart_params.with_constant_dry_temp = True
    chart.config.chart_params.with_constant_humidity = True
    chart.config.chart_params.with_constant_wet_temp = False
    chart.config.chart_params.with_constant_h = False
    chart.config.chart_params.with_constant_rh = False

    # config changes are not processed until plot
    assert chart.pressure != 100500.0
    chart.plot()
    assert chart.pressure == 100500.0

    # annotate plot
    points = {
        "exterior": (31.06, 32.9),
        "exterior_estimated": (36.7, 25.0),
        "interior": (29.42, 52.34),
    }
    convex_groups: list[ConvexGroupTuple] = [
        (["exterior", "exterior_estimated", "interior"], {}, {}),
    ]
    chart.plot_points_dbt_rh(points, convex_groups=convex_groups)

    # Save to disk
    store_test_chart(chart, "chart_overlay_minimal.svg")


def test_chart_overlay_arrows():
    """Customize a chart with some additions from a default style."""
    # Load default config
    chart = PsychroChart.create("interior")

    # Plotting
    chart.plot()

    arrows = {
        "exterior": [(31.06, 32.9), (29.06, 31.9)],
        "exterior_estimated": [(36.7, 25.0), (34.7, 30.0)],
        "interior": [(29.42, 52.34), (31.42, 57.34)],
    }
    chart.plot_arrows_dbt_rh(arrows)

    # Legend
    chart.plot_legend(markerscale=1.0, fontsize=11, labelspacing=1.3)

    # Save to disk
    store_test_chart(chart, "test_chart_overlay_arrows_1.svg")

    chart.remove_annotations()
    points_arrows = {
        "exterior": {
            "label": "Exterior",
            "style": {
                "color": [0.855, 0.004, 0.278, 0.8],
                "marker": "X",
                "markersize": 15,
            },
            "xy": [(30.06, 34.9), (31.06, 35.9)],
        },
        "exterior_estimated": {
            "label": "Estimated (Weather service)",
            "style": {
                "color": [0.573, 0.106, 0.318, 0.5],
                "marker": "x",
                "markersize": 10,
            },
            "xy": [(32.7, 27.0), (31.7, 28.0)],
        },
        "interior": {
            "label": "Interior",
            "style": {
                "color": [0.592, 0.745, 0.051, 0.9],
                "marker": "o",
                "markersize": 30,
            },
            "xy": [(29.92, 50.34), (28.92, 50.34)],
        },
    }
    chart.plot_arrows_dbt_rh(points_arrows)

    # Save to disk
    store_test_chart(chart, "test_chart_overlay_arrows_2.svg")


def test_chart_overlay_convexhull():
    """Customize a chart with group of points."""
    # Load config & customize chart
    chart = PsychroChart.create("minimal")
    chart.config.limits.pressure_kpa = 90.5
    assert chart.pressure != 90500.0

    # Plotting
    chart.plot()
    assert chart.pressure == 90500.0

    points = {
        "exterior": (31.06, 32.9),
        "exterior_estimated": (36.7, 25.0),
        "interior": (29.42, 52.34),
    }

    convex_groups_bad: list[ConvexGroupTuple] = [
        (["exterior", "interior"], {}, {}),
    ]
    with pytest.raises(ValueError):
        chart.plot_points_dbt_rh(points, convex_groups=convex_groups_bad)

    convex_groups_bad_2 = [
        {
            "point_names": ["exterior", "interior"],
            "line_style": {"color": "green", "lw": 0},
            "fill_style": {"color": "darkgreen"},
        }
    ]
    with pytest.raises(ValueError):
        chart.plot_points_dbt_rh(points, convex_groups=convex_groups_bad_2)

    convex_groups_ok: list[ConvexGroupTuple] = [
        (["exterior", "exterior_estimated", "interior"], {}, {}),
    ]
    chart.plot_points_dbt_rh(points, convex_groups=convex_groups_ok)

    # Legend
    chart.plot_legend(markerscale=1.0, fontsize=11, labelspacing=1.3)

    # Save to disk
    store_test_chart(chart, "chart_overlay_test_convexhull.svg")


def test_overlay_a_lot_of_points():
    """Customize a chart with two cloud of points."""
    # Load config & customize chart
    chart = PsychroChart.create("minimal")
    chart.config.figure.dpi = 100
    chart.config.limits.pressure_kpa = 90.5
    assert chart.pressure != 90500.0

    # Plotting
    chart.plot()
    assert chart.pressure == 90500.0

    # Create a lot of points
    num_samples = 100000
    theta = np.linspace(0, 2 * np.pi, num_samples)
    r = np.random.rand(num_samples)
    x, y = 7 * r * np.cos(theta) + 25, 20 * r * np.sin(theta) + 50

    scatter_style_1 = {
        "s": 20,
        "alpha": 0.02,
        "color": "darkblue",
        "marker": "o",
    }
    scatter_style_2 = {
        "s": 10,
        "alpha": 0.04,
        "color": "darkorange",
        "marker": "+",
    }
    x2, y2 = x + 5, y - 20

    points = {
        "test_original": {
            "label": "Original",
            "style": scatter_style_1,
            "xy": (x, y),
        },
        "test_displaced": (x2, y2),
    }
    chart.plot_points_dbt_rh(points, scatter_style=scatter_style_2)
    chart.plot_legend(markerscale=1.0, fontsize=11, labelspacing=1.3)

    # Save to disk
    chart.save(TEST_BASEDIR / "chart_overlay_test_lot_of_points.png")
    # uncomment to generate a BIG SVG file
    # store_test_chart(chart, "chart_overlay_test_lot_of_points.svg", png=True)
