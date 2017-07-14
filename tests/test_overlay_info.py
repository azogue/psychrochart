# -*- coding: utf-8 -*-
"""
Tests plotting

"""
import os
from unittest import TestCase


basedir = os.path.dirname(os.path.abspath(__file__))


class TestsPsychroOverlay(TestCase):
    """Unit Tests to check the addition of info to psychrometric charts."""

    def test_custom_psychrochart(self):
        """Customize a chart with some additions"""
        from psychrochart.chart import PsychroChart

        chart = PsychroChart("minimal")

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
                    }
                ]
        }
        chart.append_zones(zones_conf)

        # Plotting
        ax = chart.plot()

        # Vertical lines
        t_min, t_opt, t_max = 16, 23, 30
        chart.plot_vertical_dry_bulb_temp_line(
            ax, t_min, {"color": [0.0, 0.125, 0.376], "lw": 2, "ls": ':'},
            '  TOO COLD ({}°C)'.format(t_min), ha='left', loc=0., fontsize=14)
        chart.plot_vertical_dry_bulb_temp_line(
            ax, t_opt, {"color": [0.475, 0.612, 0.075], "lw": 2, "ls": ':'})
        chart.plot_vertical_dry_bulb_temp_line(
            ax, t_max, {"color": [1.0, 0.0, 0.247], "lw": 2, "ls": ':'},
            'TOO HOT ({}°C)  '.format(t_max), ha='right', loc=1,
            reverse=True, fontsize=14)

        points = {'exterior': {'label': 'Exterior',
                               'style': {'color': [0.855, 0.004, 0.278, 0.8],
                                         'marker': 'X', 'markersize': 15},
                               'xy': (31.06, 32.9)},
                  'exterior_estimated': {
                      'label': 'Estimated (Weather service)',
                      'style': {'color': [0.573, 0.106, 0.318, 0.5],
                                'marker': 'x', 'markersize': 10},
                      'xy': (36.7, 25.0)},
                  'interior': {'label': 'Interior',
                               'style': {'color': [0.592, 0.745, 0.051, 0.9],
                                         'marker': 'o', 'markersize': 30},
                               'xy': (29.42, 52.34)}}
        connectors = [{'start': 'exterior',
                       'end': 'exterior_estimated',
                       'style': {'color': [0.573, 0.106, 0.318, 0.7],
                                 "linewidth": 2, "linestyle": "-."}},
                      {'start': 'exterior',
                       'end': 'interior',
                       'style': {'color': [0.855, 0.145, 0.114, 0.8],
                                 "linewidth": 2, "linestyle": ":"}}]

        points_plot = chart.plot_points_dbt_rh(ax, points, connectors)
        print('Points in chart: %s' % points_plot)

        # Legend
        chart.plot_legend(
            ax, markerscale=.7,
            frameon=False, fontsize=10, labelspacing=1.2)

        # Save to disk
        path_svg = os.path.join(
            basedir, '..', 'docs', 'chart_overlay_style_minimal.svg')
        ax.get_figure().savefig(path_svg)

    def test_custom_psychrochart_2(self):
        """Customize a chart with some additions from a default style."""
        from psychrochart.chart import PsychroChart
        from psychrochart.util import load_config

        # Load config
        config = load_config("minimal")

        # Customization
        config['figure']['x_label'] = None
        config['figure']['y_label'] = None
        config['saturation']['linewidth'] = 3
        config['chart_params']['with_constant_dry_temp'] = False
        config['chart_params']['with_constant_humidity'] = False
        config['chart_params']['with_constant_wet_temp'] = False
        config['chart_params']['with_constant_h'] = False

        # Chart creation
        chart = PsychroChart(config)

        # Zones:
        zones_conf = {
            "zones":
                [
                    {
                        "zone_type": "xy-points",
                        "style": {"linewidth": 2,
                                  "linestyle": "--",
                                  # "color": [0.831, 0.839, 0.0],
                                  "edgecolor": [0.498, 0.624, 0.8],
                                  "facecolor": [0.498, 0.624, 1.0, 0.3]
                                  },
                        "points_x": [23, 28, 28, 24, 23],
                        "points_y": [1, 3, 4, 4, 2],
                        "label": "Custom"
                    }
                ]
        }
        chart.append_zones(zones_conf)

        # Plotting
        ax = chart.plot()

        points = {'exterior': (31.06, 32.9),
                  'exterior_estimated': (36.7, 25.0),
                  'interior': (29.42, 52.34)}

        points_plot = chart.plot_points_dbt_rh(ax, points)
        print('Points in chart: %s' % points_plot)

        # Legend
        chart.plot_legend(
            ax, markerscale=1., fontsize=11, labelspacing=1.3)

        # Save to disk
        path_svg = os.path.join(
            basedir, 'chart_overlay_test.svg')
        ax.get_figure().savefig(path_svg)
