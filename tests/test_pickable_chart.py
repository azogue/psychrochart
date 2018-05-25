# -*- coding: utf-8 -*-
"""
Test that Psychrochart object is pickable

"""
import os
from unittest import TestCase

from psychrochart.agg import PsychroChart
import pickle


basedir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'charts')
os.makedirs(basedir, exist_ok=True)


class TestsPicklePsychrochart(TestCase):
    """Unit Tests to check the psychrometric charts."""

    def test_0_pickle_psychrochart(self):
        """Test the plot custom styling with JSON files/dicts."""
        path_svg = os.path.join(
            basedir, 'test_to_pickle.svg')
        chart = PsychroChart()
        chart.save(path_svg)
        chart.close_fig()

        with open(os.path.join(basedir, 'chart.pickle'), 'wb') as f:
            pickle.dump(chart, f)

    def test_1_unpickle_psychrochart(self):
        """Test the plot custom styling with dicts."""
        with open(os.path.join(basedir, 'chart.pickle'), 'rb') as f:
            chart = pickle.load(f)

        path_svg = os.path.join(
            basedir, 'test_from_pickle.svg')
        chart.save(path_svg)
        chart.close_fig()

    def test_2_compare_psychrocharts(self):
        """Test the plot custom styling with dicts."""
        with open(os.path.join(basedir, 'test_to_pickle.svg')) as f:
            chart_1 = f.read()
        with open(os.path.join(basedir, 'test_from_pickle.svg')) as f:
            chart_2 = f.read()

        assert len(chart_1) == len(chart_2)
        # assert chart_1 == chart_2  # ids change in every plot
