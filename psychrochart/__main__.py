# -*- coding: utf-8 -*-
"""
A python library to make psychrometric charts and overlay information in them.

"""
from psychrochart.psychroplot import plot_psychrochart, plt


def main():
    """CLI entry point to show the default psychrometric chart."""
    plot_psychrochart()
    plt.show()


if __name__ == '__main__':
    main()
