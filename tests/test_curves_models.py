"""Tests objects to handle psychrometric curves."""
import matplotlib.pyplot as plt
import numpy as np

from psychrochart import PsychroChart
from psychrochart.models.curves import PsychroCurve
from psychrochart.models.styles import CurveStyle


def test_curve_serialization():
    """Test the PsychroCurve object."""
    x_data = np.arange(0, 50, 1)
    y_data = np.arange(0, 50, 1)
    style = CurveStyle(color="k", linewidth=0.5)

    curve = PsychroCurve(x_data=x_data, y_data=y_data, style=style)

    # Dict export and import:
    d_curve = curve.dict()
    curve_d = PsychroCurve.validate(d_curve)
    assert curve == curve_d

    # JSON import export
    json_curve = curve.json()
    curve_js = PsychroCurve.parse_raw(json_curve)
    assert isinstance(curve_js, PsychroCurve)
    assert repr(curve_js) == "<PsychroCurve 50 values>"
    assert curve == curve_js


def test_plot_single_curves():
    """Test the plotting of PsychroCurve objects."""
    x_data = np.arange(0, 50, 1)
    y_data = np.arange(0, 50, 1)
    style = CurveStyle(color="k", linewidth=0.5)
    curve = PsychroCurve(x_data=x_data, y_data=y_data, style=style)

    # Plotting
    ax = plt.subplot()
    curve.plot_curve(ax)

    # Vertical line
    vertical_curve = PsychroCurve(x_data=[25, 25], y_data=[2, 48], style=style)
    vertical_curve.plot_curve(ax)

    # Add label
    vertical_curve.add_label(ax, "TEST", va="baseline", ha="center")


def test_string_representation_for_psychrochart_objs():
    """Check the string representation of objects."""
    obj_repr = "<PsychroChart [0->50 °C, 0->40 gr/kg_da]>"
    data_chart = PsychroChart.create()
    assert repr(data_chart) == obj_repr
    assert (
        repr(data_chart.constant_rh_data)
        == "<11 PsychroCurves (label: Constant relative humidity)>"
    )
    assert (
        repr(data_chart.constant_v_data)
        == "<10 PsychroCurves (label: Constant specific volume)>"
    )
    assert (
        repr(data_chart.constant_wbt_data)
        == "<9 PsychroCurves (label: Constant wet bulb temperature)>"
    )
    assert (
        repr(data_chart.constant_h_data)
        == "<30 PsychroCurves (label: Constant enthalpy)>"
    )
    assert (
        repr(data_chart.constant_dry_temp_data)
        == "<50 PsychroCurves (label: Dry bulb temperature)>"
    )
    assert repr(data_chart.saturation) == "<1 PsychroCurves>"
    assert repr(data_chart.saturation.curves[0]) == "<PsychroCurve 51 values>"
