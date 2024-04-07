import matplotlib.pyplot as plt

from psychrochart import PsychroChart
from psychrochart.chart_entities import ChartRegistry
from psychrochart.plot_logic import apply_axis_styling, plot_chart


def test_registry_fill_on_plot():
    chart = PsychroChart.create()
    assert chart.config.has_changed
    assert not chart.artists.saturation
    assert not chart.artists.constant_humidity
    assert not chart.artists.zones
    assert not chart.artists.layout
    assert not chart.constant_rh_data
    chart.process_chart()
    assert not chart.config.has_changed
    assert chart.constant_rh_data is not None
    assert not chart.artists.constant_humidity

    # `plot_chart` functional method
    ax = plt.subplot(position=chart.config.figure.position)
    artists_layout = apply_axis_styling(chart.config, ax)
    new_registry = plot_chart(chart, ax)
    assert isinstance(new_registry, ChartRegistry)
    assert new_registry.saturation
    assert new_registry.constant_humidity
    assert new_registry.zones
    assert not new_registry.layout
    assert not new_registry.annotations

    # chart registry unchanged!
    assert not chart.artists.saturation
    assert not chart.artists.constant_humidity
    assert not chart.artists.zones
    assert not chart.artists.layout

    # with `.plot` method of chart, registry is updated
    chart.plot()
    assert chart.artists.saturation.keys() == new_registry.saturation.keys()
    assert (
        chart.artists.constant_humidity.keys()
        == new_registry.constant_humidity.keys()
    )
    assert chart.artists.zones.keys() == new_registry.zones.keys()
    assert not chart.artists.annotations
    assert all(k in chart.artists.layout for k in artists_layout)
