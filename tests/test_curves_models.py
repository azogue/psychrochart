"""Tests objects to handle psychrometric curves."""
import matplotlib.pyplot as plt
import numpy as np
import pytest

from psychrochart import PsychroChart
from psychrochart.models.curves import PsychroCurve
from psychrochart.models.styles import CurveStyle
from psychrochart.plot_logic import add_label_to_curve, plot_curve


def test_curve_validation():
    x_data = np.arange(0, 50, 1)
    y_data = np.arange(0, 50, 1)
    raw_style = {"color": "blue", "lw": 0.5}

    # pydantic validation for raw dicts
    curve = PsychroCurve.validate(
        {"x_data": x_data, "y_data": y_data, "style": raw_style, "label": "T1"}
    )
    assert (curve.x_data == x_data).all()
    assert curve.label == "T1"
    assert isinstance(curve.style, CurveStyle)
    assert isinstance(curve.style, CurveStyle)
    assert curve.curve_id == "T1"

    # also for styling
    style = CurveStyle.validate(raw_style)
    assert style.color[2] == 1.0
    assert style.linewidth == 0.5

    with pytest.raises(ValueError):
        # curves need a label or an internal value
        PsychroCurve(x_data=x_data, y_data=y_data, style=style)

    with pytest.raises(ValueError):
        # data should have the same length
        PsychroCurve(x_data=x_data[:-1], y_data=y_data, style=style, label="T")

    with pytest.raises(ValueError):
        # and not be empty!
        PsychroCurve(
            x_data=np.array([]), y_data=np.array([]), style=style, label="T"
        )

    # no label (:=no presence on legend if enabled), but an internal value
    curve = PsychroCurve(
        x_data=x_data, y_data=y_data, style=style, internal_value=42
    )
    assert curve.curve_id == "42"


def test_curve_serialization():
    """Test the PsychroCurve object."""
    x_data = np.arange(0, 50, 1)
    y_data = np.arange(0, 50, 1)
    style = CurveStyle(color="k", linewidth=0.5)
    curve = PsychroCurve(
        x_data=x_data, y_data=y_data, style=style, internal_value=2
    )

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
    curve = PsychroCurve(x_data=x_data, y_data=y_data, style=style, label="T1")

    # Plotting
    ax = plt.subplot()
    plot_curve(curve, ax)

    # Vertical line
    vertical_curve = PsychroCurve(
        x_data=[25, 25], y_data=[2, 48], style=style, internal_value=25
    )
    plot_curve(vertical_curve, ax)

    # Add label
    add_label_to_curve(vertical_curve, ax, "TEST", va="baseline", ha="center")


def test_string_representation_for_psychrochart_objs():
    """Check the string representation of objects."""
    obj_repr = "<PsychroChart [0->50 °C, 0->40 gr/kg_da]>"
    data_chart = PsychroChart.create()
    data_chart.process_chart()
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
    assert repr(data_chart.saturation) == "<PsychroCurve 51 values>"
