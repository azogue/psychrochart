# -*- coding: utf-8 -*-
"""
Tests plotting

"""
import os
from unittest import TestCase

from psychrochart.chart import PsychroChart


basedir = os.path.dirname(os.path.abspath(__file__))


class TestsPsychroPlot(TestCase):
    """Unit Tests to check the psychrometric charts."""

    def test_default_psychrochart(self):
        """Test the plot custom styling with JSON files/dicts."""
        path_svg_default = os.path.join(
            basedir, 'test_default_psychrochart.svg')
        chart = PsychroChart()
        chart.save(path_svg_default)

    def test_custom_style_psychrochart(self):
        """Test the plot custom styling with dicts."""
        custom_style = {
            "figure": {
                "figsize": [12, 8],
                "base_fontsize": 12,
                "title": None,
                "x_label": None,
                "y_label": None,
                "partial_axis": False
            },
            "limits": {
                "range_temp_c": [15, 25],
                "range_humidity_g_kg": [0, 20],
                "altitude_m": 900,
                "step_temp": .2
            },
            "saturation": {"color": [0, .3, 1.], "linewidth": 2},
            "constant_rh": {"color": [0.0, 0.498, 1.0, .7], "linewidth": 2.5,
                            "linestyle": ":"},

            "chart_params": {
                "with_constant_rh": True,
                "constant_rh_curves": [25, 50, 75],
                "constant_rh_labels": [25, 50, 75],

                "with_constant_v": False,
                "with_constant_h": False,
                # "with_constant_wet_temp": False,
                "range_wet_temp": [-10, 30],
                # "constant_wet_temp_labels": [5, 10, 15, 20],
                # "with_constant_dry_temp": False,
                # "with_constant_humidity": False,
                "with_zones": False
            }
        }
        chart = PsychroChart(custom_style)
        chart.plot()
        chart.plot_legend()

        path_png = os.path.join(
            basedir, 'test_custom_psychrochart.png')
        chart.save(path_png, transparent=True)

    def test_default_styles_psychrochart(self):
        """Test the plot custom styling with JSON files."""
        path_svg_ashrae = os.path.join(
            basedir, 'test_ashrae_psychrochart.svg')
        chart = PsychroChart("ashrae")
        chart.plot()
        chart.save(path_svg_ashrae)
        chart.save(path_svg_ashrae.replace('svg', 'png'), transparent=True)

        path_svg_2 = os.path.join(
            basedir, 'test_interior_psychrochart.svg')
        chart = PsychroChart("interior")
        chart.plot()
        chart.plot_legend(
            markerscale=.7, frameon=False, fontsize=10, labelspacing=1.2)
        chart.save(path_svg_2)

        path_svg_3 = os.path.join(
            basedir, 'test_minimal_psychrochart.svg')
        chart = PsychroChart("minimal")
        chart.plot()
        chart.plot_legend()
        chart.save(path_svg_3)
