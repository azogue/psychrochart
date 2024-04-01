from psychrochart import ChartZone, load_config, PsychroChart
from psychrochart.models.styles import ZoneStyle
from tests.conftest import store_test_chart

_RAW_ZONE_H_RH = {
    "points_x": [40, 55],
    "points_y": [40, 80],
    "label": "Zone 'enthalpy-rh' 1",
    "zone_type": "enthalpy-rh",
    "style": {
        "edgecolor": [0.498, 0.624, 0.8],
        "facecolor": "red",
        "linewidth": 0.5,
        "linestyle": "--",
        "alpha": 0.3,
    },
}
_RAW_ZONE_V_RH = {
    "points_x": [0.88, 0.91],
    "points_y": [30, 90],
    "label": "Zone 'volume-rh'",
    "zone_type": "volume-rh",
    "style": {
        "edgecolor": [0.498, 0.624, 0.8],
        "facecolor": "green",
        "linewidth": 0.5,
        "linestyle": "--",
        "alpha": 0.3,
    },
}


def test_rh_delimited_zones():
    config = load_config("minimal")
    # zoom in to make zones cross axis
    config.limits.range_temp_c = (10, 35)
    config.limits.range_humidity_g_kg = (5, 15)
    config.limits.step_temp = 1

    config.chart_params.with_constant_humidity = True
    config.chart_params.constant_humid_step = 1.0
    config.chart_params.constant_humid_label_step = 1.0
    config.chart_params.with_constant_dry_temp = True
    config.chart_params.constant_temp_step = 1.0
    config.chart_params.constant_temp_label_step = 1.0
    config.chart_params.range_vol_m3_kg = (0.80, 1)
    config.chart_params.constant_v_step = 0.01
    config.chart_params.constant_v_labels = [0.88, 0.9, 0.92, 0.94]

    # config.constant_rh.marker = 'o'
    config.constant_rh.linewidth = 1.0
    config.constant_h.linewidth = 0.75
    config.constant_v.linewidth = 0.75
    config.chart_params.with_constant_h = True
    config.chart_params.range_h = (10, 100)
    config.chart_params.constant_h_step = 5
    config.chart_params.constant_h_labels = [40, 55]

    hrh_zone1 = ChartZone.model_validate(_RAW_ZONE_H_RH)
    hrh_zone2 = ChartZone(
        zone_type="enthalpy-rh",
        points_x=[20, 35],
        points_y=[50, 95],
        label="Zone 'enthalpy-rh' 2",
        style=ZoneStyle(
            edgecolor=config.constant_h.color,
            facecolor="yellow",
            linewidth=0.5,
        ),
    )
    hrh_zone3 = ChartZone(
        zone_type="enthalpy-rh",
        points_x=[50, 65],
        points_y=[20, 60],
        label="Zone 'enthalpy-rh' 3",
        style=ZoneStyle(
            edgecolor=config.saturation.color,
            facecolor="red",
            linewidth=0.5,
            alpha=0.3,
        ),
    )
    vrh_zone1 = ChartZone(**_RAW_ZONE_V_RH)
    chart = PsychroChart.create(
        config,
        extra_zones={"zones": [hrh_zone1, hrh_zone2, hrh_zone3, vrh_zone1]},
    )
    chart.plot_legend()
    store_test_chart(chart, "chart-zones-enthalpy-volume-rh.svg")
    assert "chart_legend" in chart.artists.layout
    assert chart.artists.zones

    # zoom out to include full zones inside limits
    config.limits.range_temp_c = (-5, 50)
    config.limits.range_humidity_g_kg = (0, 25)
    chart.plot_legend()
    store_test_chart(chart, "chart-zones-enthalpy-volume-rh-zoom-out.svg")
    assert "chart_legend" in chart.artists.layout
    assert chart.artists.zones

    # remove zones and legend
    chart.remove_zones()
    chart.remove_legend()
    svg_no_annot = chart.make_svg()
    assert not chart.artists.zones
    assert "chart_legend" not in chart.artists.layout
    assert "chart_legend" not in svg_no_annot
    assert "enthalpy-rh" not in svg_no_annot
    assert "volume-rh" not in svg_no_annot


def test_invisible_zones(caplog):
    low_left_vrh_zone = ChartZone(
        zone_type="volume-rh",
        points_x=[0.8, 0.82],
        points_y=[20, 70],
        label="test_hidden_vrh",
        style=ZoneStyle(
            edgecolor="darkred",
            facecolor="red",
            linewidth=3,
            alpha=0.5,
        ),
    )
    top_right_hrh_zone = ChartZone(
        zone_type="enthalpy-rh",
        points_x=[130, 135],
        points_y=[40, 90],
        label="test_hidden_hrh",
        style=ZoneStyle(
            edgecolor="none",
            facecolor="green",
            linewidth=0.5,
            alpha=0.3,
        ),
    )
    chart = PsychroChart.create(
        extra_zones={"zones": [low_left_vrh_zone, top_right_hrh_zone]},
    )
    caplog.clear()

    svg_out = chart.make_svg()
    assert '<g id="zone_enthalpy_rh_test_hidden_hrh"' in svg_out
    assert '<g id="zone_volume_rh_test_hidden_vrh"' in svg_out
    assert len(caplog.messages) == 0
    assert chart.artists.zones

    # zoom in to make zones invisible in plot
    chart.config.limits.range_temp_c = (25, 35)
    chart.config.limits.range_humidity_g_kg = (0, 18)
    svg_zoom = chart.make_svg()
    assert '<g id="zone_enthalpy_rh_test_hidden_hrh"' not in svg_zoom
    assert '<g id="zone_volume_rh_test_hidden_vrh"' not in svg_zoom
    assert len(caplog.messages) >= 2
    assert not chart.artists.zones
    assert chart.plot_over_saturated_zone() is None


def test_max_humid_delimited_zones():
    config = load_config("minimal")
    config.limits.range_temp_c = (10, 22)
    config.limits.range_humidity_g_kg = (5, 20)
    config.limits.step_temp = 1

    config.chart_params.with_constant_humidity = True
    config.chart_params.constant_humid_step = 1.0
    config.chart_params.constant_humid_label_step = 1.0
    config.chart_params.with_constant_dry_temp = True
    config.chart_params.constant_temp_step = 1.0
    config.chart_params.constant_temp_label_step = 1.0
    config.chart_params.range_vol_m3_kg = (0.80, 1)
    config.chart_params.constant_v_step = 0.01
    config.chart_params.constant_v_labels = [0.88, 0.9, 0.92, 0.94]

    config.constant_rh.linewidth = 1.0
    config.constant_h.linewidth = 0.75
    config.constant_v.linewidth = 0.75
    config.chart_params.with_constant_h = True
    config.chart_params.range_h = (10, 100)
    config.chart_params.constant_h_step = 5
    config.chart_params.constant_h_labels = [40, 55]

    wmax_z1 = ChartZone(
        zone_type="dbt-wmax",
        points_x=[12, 40],
        points_y=[7, 13],
        label="Zone w_max 1",
        style=ZoneStyle(
            edgecolor=config.constant_h.color,
            facecolor="yellow",
            linewidth=0.5,
        ),
    )
    wmax_z2 = ChartZone(
        zone_type="dbt-wmax",
        points_x=[5, 30],
        points_y=[0, 8],
        label="Zone w_max 2",
        style=ZoneStyle(
            edgecolor=config.constant_h.color,
            facecolor="#aa000033",
            linewidth=1.5,
        ),
    )
    wmax_z3 = ChartZone(
        zone_type="dbt-wmax",
        points_x=[36, 45],
        points_y=[0, 24],
        label="Zone w_max 3",
        style=ZoneStyle(
            edgecolor=config.constant_h.color,
            facecolor="#00aa0033",
            linewidth=1.5,
        ),
    )
    wmax_z4 = ChartZone(
        zone_type="dbt-wmax",
        points_x=[20, 60],
        points_y=[17, 19],
        label="Zone w_max 4",
        style=ZoneStyle(
            edgecolor=config.constant_h.color,
            facecolor="#0000aa33",
            linewidth=1.5,
        ),
    )
    config.chart_params.zones = [wmax_z1, wmax_z2, wmax_z3, wmax_z4]

    chart = PsychroChart.create(config)
    store_test_chart(chart, "chart-zones-wmax.svg")
    assert len(chart.artists.zones) == 6

    # zoom out to include full zones inside limits
    config.limits.range_temp_c = (6, 50)
    config.limits.range_humidity_g_kg = (0, 25)
    store_test_chart(chart, "chart-zones-wmax-zoom-out.svg")
    assert chart.artists.zones
    assert len(chart.artists.zones) == 8

    # remove zones
    chart.remove_zones()
    svg_no_annot = chart.make_svg()
    assert not chart.artists.zones
    assert "Zone w_max" not in svg_no_annot
    assert "dbt-wmax" not in svg_no_annot


def test_sat_no_sat_zones():
    chart = PsychroChart.create("minimal")
    chart.config.chart_params.zones.append(
        ChartZone(
            zone_type="dbt-wmax",
            points_x=[chart.config.dbt_min, chart.config.dbt_max],
            points_y=[chart.config.w_min, chart.config.w_max],
            style=ZoneStyle(edgecolor="k", facecolor="#e4a039", linewidth=0),
        )
    )
    chart.plot_over_saturated_zone(color_fill="#5A90E4")
    store_test_chart(chart, "chart-saturation-zones.svg")
