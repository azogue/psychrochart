# -*- coding: utf-8 -*-
"""
A python library to make psychrometric charts and overlay information in them.

"""
# from matplotlib.pyplot import show
from psychrochart.psychroplot import plot_psychrochart


def main():
    """CLI entry point to show the default psychrometric chart."""
    plot_psychrochart()
    # show()


if __name__ == '__main__':
    main()
