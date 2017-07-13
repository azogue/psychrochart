# -*- coding: utf-8 -*-
"""
Tests plotting

"""
import matplotlib.pyplot as plt
import os
from unittest import TestCase



basedir = os.path.dirname(os.path.abspath(__file__))


class TestsPsychroOverlay(TestCase):
    """Unit Tests to check the addition of info to psychrometric charts."""

    def test_custom_psychrochart(self):
        """Customize a chart with some additions"""
        from psychrochart.chart import PsychroChart
        from psychrochart.chart import PsychroCurve
        from psychrochart.equations import (
            saturation_pressure_water_vapor, humidity_ratio, humidity_ratio_from_temps)

        chart = PsychroChart("minimal")

        # Vertical lines
        t_min, t_opt, t_max = 16, 23, 30
        # w_t_min = 1000 * humidity_ratio_from_temps(t_min, t_min)
        # w_t_opt = 1000 * humidity_ratio_from_temps(t_opt, t_opt)
        # w_t_max = 1000 * humidity_ratio_from_temps(t_max, t_max)
        w_t_min = 1000 * humidity_ratio(saturation_pressure_water_vapor(t_min), chart.p_atm_kpa)
        w_t_opt = 1000 * humidity_ratio(saturation_pressure_water_vapor(t_opt), chart.p_atm_kpa)
        w_t_max = 1000 * humidity_ratio(saturation_pressure_water_vapor(t_max), chart.p_atm_kpa)

        # ax.plot([t_min, t_min], [chart.w_min, w_t_min], color=[0.0, 0.125, 0.376], lw=2, ls=':')
        # ax.plot([t_opt, t_opt], [chart.w_min, w_t_opt], color=[0.475, 0.612, 0.075], lw=2, ls=':')
        # ax.plot([t_max, t_max], [w_t_max, chart.w_min], color=[1.0, 0.0, 0.247], lw=2, ls=':')

        c1 = PsychroCurve(
            [t_min, t_min], [chart.w_min, w_t_min],
            style={"color": [0.0, 0.125, 0.376], "lw":2, "ls":':'})
        c2 = PsychroCurve(
            [t_opt, t_opt], [chart.w_min, w_t_opt],
            style={"color": [0.475, 0.612, 0.075], "lw":2, "ls":':'})
        c3 = PsychroCurve(
            [t_max, t_max], [w_t_max, chart.w_min],
            style={"color": [1.0, 0.0, 0.247], "lw":2, "ls":':'})


        # Zones:
        zones_conf = {
            "zones":
                [
                    {
                        "zone_type": "dbt-rh",
                        "style": {"edgecolor": [1.0, 0.749, 0.0, 0.8],
                                  "facecolor": [1.0, 0.749, 0.0, 0.2],
                                  "linewidth": 2,
                                  "linestyle": "--"},
                        "points_x": [23, 28],
                        "points_y": [40, 60],
                        "label": "Summer"
                    },
                    {
                        "zone_type": "dbt-rh",
                        "style": {"edgecolor": [0.498, 0.624, 0.8],
                                  "facecolor": [0.498, 0.624, 1.0, 0.2],
                                  "linewidth": 2,
                                  "linestyle": "--"},
                        "points_x": [18, 23],
                        "points_y": [35, 55],
                        "label": "Winter"
                    },
                    {
                        "zone_type": "xy-points",
                        "style": {"linewidth": 2,
                                  "linestyle": "--",
                                  # "color": [0.831, 0.839, 0.0],
                                  "edgecolor": [0.498, 0.624, 0.8],
                                  "facecolor": [0.498, 0.624, 1.0, 0.3]
                                  },
                        "points_x": [23, 28, 28, 24, 23],
                        "points_y": [0, 0, 4, 4, 2],
                        "label": "Custom"
                    }
                ]
        }
        chart.append_zones(zones_conf)

        # Plotting
        ax = chart.plot()

        c1.plot(ax)
        c1.add_label(ax, 'TOO COLD ({}°C)'.format(t_min), ha='center', loc=.5)
        c2.plot(ax)
        c3.plot(ax)
        c3.add_label(ax, 'TOO HOT ({}°C)'.format(t_max), ha='center', loc=.5)

        # Save to disk
        path_svg = os.path.join(
            basedir, '..', 'docs', 'chart_overlay_style_minimal.svg')
        plt.savefig(path_svg)
        plt.close()
