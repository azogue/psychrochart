# -*- coding: utf-8 -*-
"""
Tests plotting

"""
from unittest import TestCase
import os


basedir = os.path.dirname(os.path.abspath(__file__))


class TestsPsychroPlot(TestCase):
    """Unit Tests to check the psychrometric charts."""

    def test_default_psychrochart(self):
        """Test the plot custom styling with JSON files/dicts."""
        from psychrochart.psychroplot import plot_psychrochart, plt

        path_svg_default = os.path.join(
            basedir, 'test_default_psychrochart.svg')
        plot_psychrochart()
        plt.savefig(path_svg_default)

        path_svg_ashrae = os.path.join(
            basedir, 'test_ashrae_psychrochart.svg')
        plot_psychrochart("ashrae")
        plt.savefig(path_svg_ashrae)
