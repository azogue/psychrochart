# -*- coding: utf-8 -*-
"""
Tests objects to handle psychrometric curves

"""
import json
import os
from unittest import TestCase

from psychrochart.agg import PsychroChart
from psychrochart.chart import PsychroCurve
from psychrochart.util import f_range


basedir = os.path.dirname(os.path.abspath(__file__))


class TestsPsychroCurves(TestCase):
    """Unit Tests to check the psychrometric charts."""

    def test_curve(self):
        """Test the PsychroCurve object."""
        x_data = f_range(0, 50, 1)
        y_data = f_range(0, 50, 1)
        style = {"color": "k", "linewidth": 0.5, "linestyle": "-"}

        empty_curve = PsychroCurve()
        self.assertDictEqual(empty_curve.to_dict(), {})

        curve = PsychroCurve(x_data, y_data, style)

        # Dict export and import:
        d_curve = curve.to_dict()
        curve_d = PsychroCurve(**d_curve)

        self.assertCountEqual(curve.x_data, curve_d.x_data)
        self.assertListEqual(curve.x_data, curve_d.x_data)
        self.assertCountEqual(curve.y_data, curve_d.y_data)
        self.assertListEqual(curve.y_data, curve_d.y_data)
        self.assertDictEqual(curve.style, curve_d.style)
        self.assertDictEqual(d_curve, curve_d.to_dict())

        # JSON import export
        json_curve = curve.to_json()
        curve_js = PsychroCurve()
        self.assertEqual(str(curve_js), '<Empty PsychroCurve (label: None)>')
        if curve_js:  # Existence test
            raise AssertionError()
        curve_js = curve_js.from_json(json_curve)
        if not curve_js:  # Existence test
            raise AssertionError()
        self.assertEqual(str(curve_js),
                         '<PsychroCurve 50 values (label: None)>')

        self.assertCountEqual(curve.x_data, curve_js.x_data)
        self.assertListEqual(curve.x_data, curve_js.x_data)
        self.assertCountEqual(curve.y_data, curve_js.y_data)
        self.assertListEqual(curve.y_data, curve_js.y_data)
        self.assertDictEqual(curve.style, curve_js.style)
        self.assertDictEqual(json.loads(json_curve),
                             json.loads(curve_js.to_json()))

    def test_plot_curve(self):
        """Test the plotting of PsychroCurve objects."""
        import matplotlib.pyplot as plt
        x_data = f_range(0, 50, 1)
        y_data = f_range(0, 50, 1)
        style = {"color": "k", "linewidth": 0.5, "linestyle": "-"}

        curve = PsychroCurve(x_data, y_data, style)

        # Plotting
        ax = plt.subplot()
        ax = curve.plot(ax)

        # Vertical line
        vertical_curve = PsychroCurve([25, 25], [2, 48])
        vertical_curve.plot(ax)

        # Add label
        vertical_curve.add_label(ax, 'TEST', va='baseline', ha='center')

        # plt.savefig('test_line_vert.svg')
        # plt.close()

    def test_data_psychrochart(self):
        """Check the string representation of objects."""
        obj_repr = "<PsychroChart [0->50 °C, 0->40 gr/kg_da]>"
        data_chart = PsychroChart()
        print(data_chart)
        self.assertEqual(str(data_chart), obj_repr)

        # noinspection PyUnresolvedReferences
        self.assertEqual(
            str(data_chart.constant_rh_data),
            '<11 PsychroCurves (label: Constant relative humidity)>')

        self.assertEqual(
            str(data_chart.constant_v_data),
            '<10 PsychroCurves (label: Constant specific volume)>')

        self.assertEqual(
            str(data_chart.constant_wbt_data),
            '<10 PsychroCurves (label: Constant wet bulb temperature)>')

        self.assertEqual(
            str(data_chart.constant_h_data),
            '<30 PsychroCurves (label: Constant enthalpy)>')

        self.assertEqual(
            str(data_chart.constant_dry_temp_data),
            '<50 PsychroCurves (label: Dry bulb temperature)>')

        self.assertEqual(
            str(data_chart.saturation),
            '<1 PsychroCurves (label: None)>')
        self.assertEqual(
            str(data_chart.saturation[0]),
            '<PsychroCurve 51 values (label: None)>')

