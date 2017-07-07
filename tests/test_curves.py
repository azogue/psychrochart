# -*- coding: utf-8 -*-
"""
Tests objects to handle psychrometric curves

"""
import json
import os
from unittest import TestCase

from psychrochart.chart import PsychroCurve


basedir = os.path.dirname(os.path.abspath(__file__))


class TestsPsychroCurves(TestCase):
    """Unit Tests to check the psychrometric charts."""

    def test_curve(self):
        """Test the PsychroCurve object."""
        import numpy as np

        x_data = np.arange(0, 50, 1)
        y_data = np.arange(0, 50, 1)
        style = {"color": "k", "linewidth": 0.5, "linestyle": "-"}

        curve = PsychroCurve(x_data, y_data, style)

        # Dict export and import:
        d_curve = curve.__dict__()
        curve_d = PsychroCurve(**d_curve)

        self.assertCountEqual(curve.x_data, curve_d.x_data)
        self.assertListEqual(curve.x_data.tolist(), curve_d.x_data.tolist())
        self.assertCountEqual(curve.y_data, curve_d.y_data)
        self.assertListEqual(curve.y_data.tolist(), curve_d.y_data.tolist())
        self.assertDictEqual(curve.style, curve_d.style)
        self.assertDictEqual(d_curve, curve_d.__dict__())

        # JSON import export
        json_curve = curve.to_json()
        curve_js = PsychroCurve()
        self.assertEqual(str(curve_js), '<Empty PsychroCurve (label: None)>')
        if curve_js:  # Existence test
            assert()
        curve_js = curve_js.from_json(json_curve)
        if not curve_js:  # Existence test
            assert()

        self.assertCountEqual(curve.x_data, curve_js.x_data)
        self.assertListEqual(curve.x_data.tolist(), curve_js.x_data.tolist())
        self.assertCountEqual(curve.y_data, curve_js.y_data)
        self.assertListEqual(curve.y_data.tolist(), curve_js.y_data.tolist())
        self.assertDictEqual(curve.style, curve_js.style)
        self.assertDictEqual(json.loads(json_curve),
                             json.loads(curve_js.to_json()))

    def test_plot_curve(self):
        """Test the plotting of PsychroCurve objects."""
        import matplotlib.pyplot as plt
        import numpy as np

        x_data = np.arange(0, 50, 1)
        y_data = np.arange(0, 50, 1)
        style = {"color": "k", "linewidth": 0.5, "linestyle": "-"}

        curve = PsychroCurve(x_data, y_data, style)

        # Plotting
        curve.plot()
        plt.close()

    def test_data_psychrochart(self):
        from psychrochart.chart import data_psychrochart

        data_chart = data_psychrochart()
        print(data_chart)
