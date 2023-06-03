# -*- coding: utf-8 -*-
"""
Tests plotting

"""
from unittest import TestCase

import numpy as np

from psychrochart.agg import PsychroChart
from psychrochart.util import load_config
from tests.conftest import TEST_BASEDIR, timeit


class TestsPsychroOverlay(TestCase):
    """Unit Tests to check the addition of info to psychrometric charts."""

    def test_custom_psychrochart(self):
        """Customize a chart with some additions"""

        @timeit("test_custom_psychrochart")
        def _make_chart():
            chart = PsychroChart("minimal")

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
            chart.plot_points_dbt_rh(points, connectors)

            # Legend
            chart.plot_legend(
                markerscale=0.7, frameon=False, fontsize=10, labelspacing=1.2
            )

            # Save to disk
            path_svg = TEST_BASEDIR / "chart_overlay_style_minimal.svg"
            chart.save(path_svg)

        _make_chart()

    def test_custom_psychrochart_2(self):
        """Customize a chart with some additions from a default style."""
        # Load config
        config = load_config("minimal")

        # Customization
        config["limits"]["pressure_kpa"] = 90.5
        config["figure"]["x_label"] = None
        config["figure"]["y_label"] = None
        config["saturation"]["linewidth"] = 3
        config["chart_params"]["with_constant_dry_temp"] = False
        config["chart_params"]["with_constant_humidity"] = False
        config["chart_params"]["with_constant_wet_temp"] = False
        config["chart_params"]["with_constant_h"] = False

        # Chart creation
        chart = PsychroChart(config)
        self.assertEqual(90500.0, chart.pressure)

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
                {"zone_type": "not_recognized_type", "label": "Bad zone"},
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

        convex_groups = [
            (["exterior", "exterior_estimated", "interior"], {}, {}),
        ]
        chart.plot_points_dbt_rh(points, convex_groups=convex_groups)

        # Legend
        chart.plot_legend(markerscale=1.0, fontsize=11, labelspacing=1.3)

        # Save to disk
        path_svg = TEST_BASEDIR / "chart_overlay_test.svg"
        chart.save(path_svg)

    def test_custom_psychrochart_3(self):
        """Customize a chart with some additions from a default style."""
        # Load config
        config = load_config("interior")

        # Chart creation
        chart = PsychroChart(config)

        # Zones:

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
        path_svg = TEST_BASEDIR / "test_chart_overlay_arrows_1.svg"
        chart.save(path_svg)

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
        path_svg = TEST_BASEDIR / "test_chart_overlay_arrows_2.svg"
        chart.save(path_svg)

    def test_custom_psychrochart_4(self):
        """Customize a chart with group of points."""
        # Load config
        config = load_config("minimal")

        # Customization
        config["limits"]["pressure_kpa"] = 90.5

        # Chart creation
        chart = PsychroChart(config)
        self.assertEqual(90500.0, chart.pressure)

        # Plotting
        chart.plot()

        points = {
            "exterior": (31.06, 32.9),
            "exterior_estimated": (36.7, 25.0),
            "interior": (29.42, 52.34),
        }

        convex_groups_bad = [
            (["exterior", "interior"], {}, {}),
        ]
        chart.plot_points_dbt_rh(points, convex_groups=convex_groups_bad)
        convex_groups_ok = [
            (["exterior", "exterior_estimated", "interior"], {}, {}),
        ]
        chart.plot_points_dbt_rh(points, convex_groups=convex_groups_ok)

        # Legend
        chart.plot_legend(markerscale=1.0, fontsize=11, labelspacing=1.3)

        # Save to disk
        path_svg = TEST_BASEDIR / "chart_overlay_test_convexhull.svg"
        chart.save(path_svg)

    def test_overlay_a_lot_of_points_1(self):
        """Customize a chart with group of points."""
        # Load config
        config = load_config("minimal")

        # Customization
        config["limits"]["pressure_kpa"] = 90.5

        # Chart creation
        chart = PsychroChart(config)
        self.assertEqual(90500.0, chart.pressure)

        # Plotting
        chart.plot()

        # Create a lot of points
        num_samples = 50000
        theta = np.linspace(0, 2 * np.pi, num_samples)
        r = np.random.rand(num_samples)
        x, y = 7 * r * np.cos(theta) + 25, 20 * r * np.sin(theta) + 50

        points = {"test_series_1": (x, y)}
        scatter_style = {
            "s": 5,
            "alpha": 0.1,
            "color": "darkorange",
            "marker": "+",
        }

        chart.plot_points_dbt_rh(points, scatter_style=scatter_style)

        # Save to disk
        path_png = TEST_BASEDIR / "chart_overlay_test_lot_of_points_1.png"
        chart.save(path_png)

    def test_overlay_a_lot_of_points_2(self):
        """Customize a chart with two cloud of points."""
        # Load config
        config = load_config("minimal")

        # Customization
        config["limits"]["pressure_kpa"] = 90.5

        # Chart creation
        chart = PsychroChart(config)
        self.assertEqual(90500.0, chart.pressure)

        # Plotting
        chart.plot()

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
            "test_displaced": {"label": "Displaced", "xy": (x2, y2)},
        }
        chart.plot_points_dbt_rh(points, scatter_style=scatter_style_2)
        chart.plot_legend(markerscale=1.0, fontsize=11, labelspacing=1.3)

        # Save to disk
        path_png = TEST_BASEDIR / "chart_overlay_test_lot_of_points.png"
        chart.save(path_png)
