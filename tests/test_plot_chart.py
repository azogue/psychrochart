# -*- coding: utf-8 -*-
"""
Tests plotting

"""
import matplotlib.pyplot as plt
import os
from unittest import TestCase

from psychrochart.psychroplot import plot_psychrochart


basedir = os.path.dirname(os.path.abspath(__file__))


class TestsPsychroPlot(TestCase):
    """Unit Tests to check the psychrometric charts."""

    def test_default_psychrochart(self):
        """Test the plot custom styling with JSON files/dicts."""
        path_svg_default = os.path.join(
            basedir, 'test_default_psychrochart.svg')
        plot_psychrochart()
        plt.savefig(path_svg_default)
        plt.close()

    def test_custom_psychrochart(self):
        """Test the plot custom styling with JSON files/dicts."""
        path_svg_ashrae = os.path.join(
            basedir, 'test_ashrae_psychrochart.svg')
        plot_psychrochart("ashrae")
        plt.savefig(path_svg_ashrae)
        plt.close()

        path_svg_2 = os.path.join(
            basedir, 'test_interior_psychrochart.svg')
        plot_psychrochart("interior")
        plt.savefig(path_svg_2)
        plt.close()

        path_svg_3 = os.path.join(
            basedir, 'test_minimal_psychrochart.svg')
        plot_psychrochart("minimal")
        plt.savefig(path_svg_3)
        plt.close()
