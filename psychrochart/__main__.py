# -*- coding: utf-8 -*-
"""A library to make psychrometric charts and overlay information in them."""
from psychrochart.chart import PsychroChart
import matplotlib.pyplot as plt


def main():
    """CLI entry point to show the default psychrometric chart."""
    PsychroChart().plot(ax=plt.gca())


if __name__ == '__main__':
    main()
    plt.show()
