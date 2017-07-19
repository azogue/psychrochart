# -*- coding: utf-8 -*-
"""A library to make psychrometric charts and overlay information in them."""
from psychrochart.chart import PsychroChart


def main():
    """CLI entry point to show the default psychrometric chart."""
    PsychroChart().plot()


if __name__ == '__main__':
    main()
