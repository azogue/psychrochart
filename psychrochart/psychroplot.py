# -*- coding: utf-8 -*-
"""
A python library to make psychrometric charts and overlay information in them.

"""
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from psychrochart.chart import PSYCHRO_CURVES_KEYS, data_psychrochart
from psychrochart.util import timeit


@timeit('Psychrometric chart plot')
def plot_psychrochart(styles=None) -> Axes:
    """Plot the psychrometric chart."""
    def _get_figure(figsize=(16, 9), x_label=None, y_label=None, title=None):
        """Create matplotlib figure and axis."""
        figure = plt.figure(figsize=figsize)
        figure.gca().yaxis.tick_right()
        if x_label is not None:
            plt.xlabel(x_label, fontsize=11)
        if y_label is not None:
            plt.ylabel(y_label, fontsize=11)
            figure.gca().yaxis.set_label_position("right")
        if title is not None:
            plt.title(title, fontsize=14, fontweight='bold')
        return figure

    data = data_psychrochart(styles)

    # Prepare fig & axis
    fig = _get_figure(**data.figure)
    plt.xlim([data.dbt_min, data.dbt_max])
    plt.ylim([data.w_min, data.w_max])
    ax = fig.gca()

    # Plot curves:
    # TODO getitem from data keys
    # noinspection PyProtectedMember
    data_curves = data._asdict()
    for curve_family in PSYCHRO_CURVES_KEYS:
        if data_curves.get(curve_family) is not None:
            data_curves.get(curve_family).plot(ax=ax)

    # TODO añadir zonas como overlay externo
    # Comfort zones (Spain RITE)
    if data.zones:
        for zone in data.zones:
            zone.plot()

    return ax
