# -*- coding: utf-8 -*-
"""
A python library to make psychrometric charts and overlay information in them.

"""
from matplotlib.axes import Axes

from psychrochart.chart import PsychroChart
from psychrochart.util import timeit


@timeit('Psychrometric chart plot')
def plot_psychrochart(styles=None) -> Axes:
    """Plot the psychrometric chart."""

    return PsychroChart(styles).plot()
