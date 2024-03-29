import logging

from psychrochart import PsychroChart
from psychrochart.models.config import DEFAULT_ZONES
from psychrochart.process_logic import set_unit_system
from tests.conftest import store_test_chart


def test_constant_wetbulb_temp_lines(caplog):
    set_unit_system()
    caplog.clear()
    with caplog.at_level(logging.INFO):
        chart = PsychroChart.create("minimal")
        assert len(caplog.messages) == 0, caplog.messages

        chart.config.figure.figsize = (8, 6)
        chart.config.limits.range_temp_c = (-10, 50)
        chart.config.chart_params.with_constant_v = False
        chart.config.chart_params.constant_rh_labels = []
        chart.config.chart_params.constant_h_step = 2
        chart.config.constant_h.linewidth = 0.5
        chart.config.constant_rh.linewidth = 1
        chart.config.constant_h.linestyle = ":"
        chart.config.chart_params.constant_wet_temp_step = 1
        chart.config.chart_params.with_constant_humidity = True
        chart.config.chart_params.constant_humid_step = 2
        chart.config.chart_params.range_wet_temp = [-25, 60]
        chart.config.chart_params.constant_wet_temp_labels = list(
            range(-25, 60)
        )
        store_test_chart(chart, "chart-wbt-layout-normal.svg")

        # example of saturation crossing x-axis
        chart.config.limits.range_humidity_g_kg = (10, 50)
        chart.plot_over_saturated_zone()
        store_test_chart(chart, "chart-wbt-layout-cut-xaxis.svg")

        # example of saturation crossing both axis
        chart.config.limits.range_humidity_g_kg = (15, 120)
        chart.plot_over_saturated_zone()
        store_test_chart(chart, "chart-wbt-layout-cut-both.svg")

        assert len(caplog.messages) == 0, caplog.messages

        # check plot in limits with 2 zones outside visible limits
        chart.close_fig()
        chart.append_zones(DEFAULT_ZONES)
        store_test_chart(chart, "chart-wbt-layout-cut-both-no-zones.svg")

        assert len(caplog.messages) == 2, caplog.messages
        assert "not between limits" in caplog.messages[0]
        assert "not between limits" in caplog.messages[1]


def test_wetbulb_temp_slope_change(caplog):
    set_unit_system()
    caplog.clear()
    with caplog.at_level(logging.INFO):
        chart = PsychroChart.create("minimal")
        assert len(caplog.messages) == 0, caplog.messages

        # detail wbt discontinuity
        chart.config.figure.figsize = (12, 12)
        chart.config.saturation.linewidth = 1
        chart.config.constant_rh.linewidth = 1

        chart.config.limits.range_temp_c = (-3, 12)
        chart.config.limits.range_humidity_g_kg = (0, 6)
        chart.config.chart_params.constant_rh_labels = []

        chart.config.chart_params.with_constant_v = False
        chart.config.chart_params.with_constant_h = False
        chart.config.chart_params.with_constant_humidity = True
        chart.config.chart_params.constant_humid_step = 2
        chart.config.chart_params.constant_temp_step = 1
        chart.config.chart_params.constant_temp_label_step = 1
        chart.config.chart_params.range_wet_temp = [-25, 60]
        chart.config.chart_params.constant_wet_temp_labels = list(
            range(-25, 60)
        )
        chart.config.chart_params.constant_wet_temp_step = 0.25
        wbt_labels = [-8, -7, -6, -2, -1, -0.5, 0, 0.5, 1, 2, 6, 7, 8]
        chart.config.chart_params.constant_wet_temp_labels = wbt_labels
        chart.config.chart_params.constant_wet_temp_labels_loc = 0.01

        store_test_chart(chart, "chart-wbt-discontinuity.svg")
        assert len(caplog.messages) == 0, caplog.messages
