import logging

import pytest

from psychrochart import PsychroChart
from psychrochart.models.config import ChartConfig
from psychrochart.models.parsers import PATH_STYLES


def test_default_config():
    config_default = ChartConfig()
    assert not config_default.has_changed

    config_json = ChartConfig.model_validate_json(
        (PATH_STYLES / "default_chart_config.json").read_text()
    )
    assert not config_json.has_changed

    config_style_none = PsychroChart.create().config
    assert config_style_none.has_changed

    config_style = PsychroChart.create("default").config
    assert config_style.has_changed

    assert config_default.model_dump() == config_style.model_dump()
    assert config_style_none.model_dump() == config_style.model_dump()
    assert config_json.model_dump() == config_style.model_dump()


def test_config_mutation():
    config = ChartConfig()
    with pytest.raises(TypeError):
        config.limits.range_temp_c[1] = 35

    config.limits.range_temp_c = (10, 35)
    assert config.limits.has_changed
    assert config.has_changed

    # validation is done on assignment, so colors are parsed into RGBA
    config.constant_humidity.color = "red"
    assert config.constant_humidity.color == [1.0, 0.0, 0.0, 1.0]
    config.constant_humidity.color = "#FF0000"
    assert config.constant_humidity.color == [1.0, 0.0, 0.0, 1.0]
    config.constant_humidity.color = "#FF000000"
    assert config.constant_humidity.color == [1.0, 0.0, 0.0, 0.0]

    assert config.constant_humidity.has_changed
    assert config.limits.range_temp_c == (10.0, 35.0)
    assert config.limits.has_changed
    assert config.has_changed

    config.commit_changes()
    assert not config.has_changed
    assert not config.limits.has_changed

    config.constant_humidity.color = "red"
    config.limits.altitude_m = 3500

    assert config.limits.has_changed
    assert config.constant_humidity.has_changed
    assert config.has_changed

    config.commit_changes()
    assert not config.has_changed
    assert not config.limits.has_changed
    assert not config.constant_humidity.has_changed


def test_chart_config_mutation_after_plot():
    chart = PsychroChart.create("minimal")
    chart.config.chart_params.constant_rh_labels_loc = 0.1
    assert chart.config.has_changed
    chart.config.chart_params.constant_rh_labels = [20, 40, 60, 80]
    svg_1 = chart.make_svg(metadata={"Date": None})
    assert not chart.config.has_changed

    chart.config.chart_params.constant_rh_labels_loc = 0.7
    assert chart.config.has_changed
    svg_2 = chart.make_svg(metadata={"Date": None})
    assert not chart.config.has_changed
    assert svg_1 != svg_2


def test_chart_config_outside_limits(caplog):
    with caplog.at_level(logging.INFO):
        chart = PsychroChart.create()
        assert chart.make_svg()
        assert not caplog.messages

    chart.config.limits.range_temp_c = (10, 25)
    chart.config.chart_params.range_wet_temp = (25, 50)
    chart.config.chart_params.range_vol_m3_kg = (1.28, 1.98)
    chart.config.chart_params.range_h = (200, 300)
    assert chart.config.has_changed

    with caplog.at_level(logging.WARNING):
        assert chart.make_svg()
        assert not chart.config.has_changed
        assert len(caplog.messages) == 3
