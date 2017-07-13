# -*- coding: utf-8 -*-
"""
A python library to make psychrometric charts and overlay information in them.

"""
# from matplotlib.pyplot import show
from psychrochart.chart import PsychroChart


def main():
    """CLI entry point to show the default psychrometric chart."""
    PsychroChart().plot()
    # show()


if __name__ == '__main__':
    main()
