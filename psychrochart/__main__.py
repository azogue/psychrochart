"""A library to make psychrometric charts and overlay information in them."""

import matplotlib.pyplot as plt

from psychrochart.chart import PsychroChart


def main():
    """CLI entry point to show the default psychrometric chart."""
    PsychroChart.create().plot(ax=plt.gca())


if __name__ == "__main__":
    main()
    plt.show()
