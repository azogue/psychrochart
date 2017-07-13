# -*- coding: utf-8 -*-
"""
Tests plotting

"""
import matplotlib.pyplot as plt
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
        PsychroChart().plot()
        plt.savefig(path_svg_default)
        plt.close()

    def test_custom_psychrochart(self):
        """Test the plot custom styling with JSON files/dicts."""
        path_svg_ashrae = os.path.join(
            basedir, 'test_ashrae_psychrochart.svg')
        chart = PsychroChart("ashrae")
        chart.plot()
        plt.savefig(path_svg_ashrae)
        # plt.savefig(path_svg_ashrae.replace('svg', 'png'), transparent=True)
        # plt.savefig(path_svg_ashrae.replace('svg', 'png'))
        plt.close()

        path_svg_2 = os.path.join(
            basedir, 'test_interior_psychrochart.svg')
        chart = PsychroChart("interior")
        chart.plot()
        plt.savefig(path_svg_2)
        plt.close()

        path_svg_3 = os.path.join(
            basedir, 'test_minimal_psychrochart.svg')
        chart = PsychroChart("minimal")
        chart.plot()
        plt.savefig(path_svg_3)
        plt.close()
