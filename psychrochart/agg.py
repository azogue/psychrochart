"""
A python library to make psychrometric charts and overlay information in them.

Import this module first to set matplotlib to use the Agg backend.
"""
import matplotlib

matplotlib.use("Agg")

from psychrochart.chart import PsychroChart  # noqa E401
