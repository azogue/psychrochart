from math import ceil, floor
from typing import Any

from psychrochart import PsychroChart
from psychrochart.chartdata import (
    gen_points_in_constant_relative_humidity,
)
from psychrochart.models.annots import ChartAnnots, ChartArea
from psychrochart.plot_logic import plot_annots_dbt_rh
from psychrochart.process_logic import set_unit_system
from tests.conftest import store_test_chart

_MIN_CHART_TEMPERATURE = 20
_MAX_CHART_TEMPERATURE = 27
# fmt: off
TEST_EXAMPLE_ZONES = [
    {
        "label": "Summer",
        "points_x": [23, 28],
        "points_y": [40, 60],
        "style": {
            "edgecolor": [1.0, 0.749, 0.0, 0.8],
            "facecolor": [1.0, 0.749, 0.0, 0.2],
            "linestyle": "--",
            "linewidth": 2,
        },
        "zone_type": "dbt-rh",
    },
    {
        "label": "Winter",
        "points_x": [18, 23],
        "points_y": [35, 55],
        "style": {
            "edgecolor": [0.498, 0.624, 0.8],
            "facecolor": [0.498, 0.624, 1.0, 0.2],
            "linestyle": "--",
            "linewidth": 2,
        },
        "zone_type": "dbt-rh",
    },
]
TEST_EXAMPLE_FIG_CONFIG = {
    "figsize": [16, 9],
    "partial_axis": True,
    "position": [0, 0, 1, 1],
    "title": None,
    "x_axis": {
        "color": [0.855, 0.145, 0.114],
        "linestyle": "-",
        "linewidth": 2,
    },
    "x_axis_labels": {"color": [0.855, 0.145, 0.114], "fontsize": 10},
    "x_axis_ticks": {
        "color": [0.855, 0.145, 0.114],
        "direction": "in",
        "pad": -20,
    },
    "x_label": None,
    "y_axis": {
        "color": [0.0, 0.125, 0.376],
        "linestyle": "-",
        "linewidth": 2,
    },
    "y_axis_labels": {"color": [0.0, 0.125, 0.376], "fontsize": 10},
    "y_axis_ticks": {
        "color": [0.0, 0.125, 0.376],
        "direction": "in",
        "pad": -20,
    },
    "y_label": None,
}
# fmt: on

TEST_EXAMPLE_CHART_CONFIG = {
    "chart_params": {
        "constant_h_label": None,
        "constant_h_labels": [25, 50, 75],
        "constant_h_step": 5,
        "constant_humid_label": None,
        "constant_humid_label_include_limits": False,
        "constant_humid_label_step": 1,
        "constant_humid_step": 0.5,
        "constant_rh_curves": [20, 40, 50, 60, 80],
        "constant_rh_label": None,
        "constant_rh_labels": [20, 40, 60],
        "constant_rh_labels_loc": 0.8,
        "constant_temp_label": None,
        "constant_temp_label_include_limits": False,
        "constant_temp_label_step": 5,
        "constant_temp_step": 5,
        "constant_v_label": None,
        "constant_v_labels": [0.82, 0.84, 0.86, 0.88],
        "constant_v_labels_loc": 0.01,
        "constant_v_step": 0.01,
        "constant_wet_temp_label": None,
        "constant_wet_temp_labels": [10, 15, 20],
        "constant_wet_temp_step": 5,
        "range_wet_temp": [15, 25],
        "range_h": [25, 85],
        "range_vol_m3_kg": [0.82, 0.88],
        "with_constant_dry_temp": True,
        "with_constant_h": True,
        "with_constant_humidity": True,
        "with_constant_rh": True,
        "with_constant_v": True,
        "with_constant_wet_temp": True,
        "with_zones": True,
    },
    "constant_dry_temp": {
        "color": [0.855, 0.145, 0.114, 0.7],
        "linestyle": ":",
        "linewidth": 0.75,
    },
    "constant_h": {
        "color": [0.251, 0.0, 0.502, 0.7],
        "linestyle": "-",
        "linewidth": 2,
    },
    "constant_humidity": {
        "color": [0.0, 0.125, 0.376, 0.7],
        "linestyle": ":",
        "linewidth": 0.75,
    },
    "constant_rh": {
        "color": [0.0, 0.498, 1.0, 0.7],
        "linestyle": "-.",
        "linewidth": 2,
    },
    "constant_v": {
        "color": [0.0, 0.502, 0.337, 0.7],
        "linestyle": "-",
        "linewidth": 1,
    },
    "constant_wet_temp": {
        "color": [0.498, 0.875, 1.0, 0.7],
        "linestyle": "-",
        "linewidth": 1,
    },
    "figure": TEST_EXAMPLE_FIG_CONFIG,
    "limits": {
        "range_humidity_g_kg": [0, 3],
        "range_temp_c": [-30, 10],
        "step_temp": 0.5,
        "pressure_kpa": 101.42,
    },
    "saturation": {
        "color": [0.855, 0.145, 0.114],
        "linestyle": "-",
        "linewidth": 5,
    },
    "zones": TEST_EXAMPLE_ZONES,
}

_EXAMPLE_SENSOR_POINTS = {
    "Aseo": {
        "xy": (20.63, 55.86),
        "label": "Aseo",
        "style": {"color": "#007bff", "alpha": 0.9, "markersize": 8},
    },
    "Cocina": {
        "xy": (20.15, 55.38),
        "label": "Cocina",
        "style": {"alpha": 0.9, "color": "#F15346", "markersize": 9},
    },
    "Dormitorio (ESP)": {
        "xy": (20.0, 59.1),
        "label": "Dormitorio (ESP)",
        "style": {"alpha": 0.9, "color": "darkgreen", "markersize": 10},
    },
    "Dormitorio": {
        "xy": (19.56, 61.84),
        "label": "Dormitorio",
        "style": {"alpha": 0.9, "color": "#51E81F", "markersize": 10},
    },
    "Estudio": {
        "xy": (20.7, 55.4),
        "label": "Estudio",
        "style": {"alpha": 0.9, "color": "#FFA067", "markersize": 9},
    },
    "Office": {
        "xy": (20.8, 53.0),
        "label": "Office",
        "style": {"alpha": 0.9, "color": "#bb1247", "markersize": 12},
    },
    "Office-Window": {
        "xy": (20.36, 64.33),
        "label": "Office-Window",
        "style": {"alpha": 0.9, "color": "#bb2b1e", "markersize": 12},
    },
    "Sofa": {
        "xy": (22.12, 52.07),
        "label": "Sofa",
        "style": {"alpha": 0.8, "color": "#E3DB55", "markersize": 10},
    },
    "Galeria (sombra)": {
        "xy": (15.51, 85.57),
        "label": "Galeria (sombra)",
        "style": {"alpha": 0.9, "color": "#fb6150", "markersize": 11},
    },
    "Terraza": {
        "xy": (17.1, 99.6),
        "label": "Terraza",
        "style": {"alpha": 0.7, "color": "#E37207", "markersize": 12},
    },
    "Terraza (sombra)": {
        "xy": (15.89, 85.48),
        "label": "Terraza (sombra)",
        "style": {"alpha": 0.9, "color": "#CC9706", "markersize": 11},
    },
}
_EXAMPLE_SENSOR_ZONES = [
    (
        [
            "Aseo",
            "Cocina",
            "Dormitorio (ESP)",
            "Dormitorio",
            "Estudio",
            "Office",
            "Office-Window",
            "Sofa",
        ],
        {"color": "darkgreen", "lw": 2, "alpha": 0.5, "ls": ":"},
        {"color": "green", "lw": 0, "alpha": 0.3},
    ),
    (
        ["Galeria (sombra)", "Terraza", "Terraza (sombra)"],
        {"color": "#E37207", "lw": 1, "alpha": 0.5, "ls": "--"},
        {"color": "#E37207", "lw": 0, "alpha": 0.2},
    ),
]


def _get_dynamic_limits(points: dict[str, Any], pressure: float = 101325.0):
    pairs_t_rh = [point["xy"] for point in points.values()]
    values_t = [p[0] for p in pairs_t_rh]
    values_w = gen_points_in_constant_relative_humidity(
        values_t, [p[1] for p in pairs_t_rh], pressure
    )

    min_temp = min(floor((min(values_t) - 1) / 3) * 3, _MIN_CHART_TEMPERATURE)
    max_temp = max(ceil((max(values_t) + 1) / 3) * 3, _MAX_CHART_TEMPERATURE)
    w_min = min(floor((min(values_w) - 1) / 3) * 3, 5.0)
    w_max = ceil(max(values_w)) + 2
    return min_temp, max_temp, w_min, w_max


def test_ha_addon_psychrochart():
    set_unit_system()
    chart_config = TEST_EXAMPLE_CHART_CONFIG.copy()
    t_min, t_max, w_min, w_max = _get_dynamic_limits(_EXAMPLE_SENSOR_POINTS)
    chart_config["limits"].update(  # type: ignore[attr-defined]
        {
            "range_temp_c": (t_min, t_max),
            "range_humidity_g_kg": (w_min, w_max),
        }
    )
    chart = PsychroChart.create(chart_config)
    chart.append_zones()
    chart_annots = chart.plot_points_dbt_rh(
        _EXAMPLE_SENSOR_POINTS, convex_groups=_EXAMPLE_SENSOR_ZONES
    )
    assert isinstance(chart_annots, ChartAnnots)
    chart.plot_legend(
        frameon=False, fontsize=15, labelspacing=0.8, markerscale=0.8
    )
    store_test_chart(
        chart, "test_ha_addon_psychrochart.svg", png=True, svg_rsc=True
    )

    chart_annots.areas.pop(0)
    chart_annots.areas.append(
        ChartArea(
            point_names=[
                "Galeria (sombra)",
                "Aseo",
                "Cocina",
                "Dormitorio (ESP)",
                "Dormitorio",
                "Estudio",
                "Office",
                "Terraza (sombra)",
            ],
            line_style={"color": "#c335e3", "lw": 1, "alpha": 0.5, "ls": "--"},
            fill_style={"color": "#aa89e3", "lw": 0, "alpha": 0.2},
        )
    )
    chart.plot()
    plot_annots_dbt_rh(chart.axes, chart_annots)
    chart.plot_legend(
        frameon=False, fontsize=15, labelspacing=0.8, markerscale=0.8
    )
    store_test_chart(chart, "test_ha_addon_psychrochart-2.svg", png=True)

    chart_annots.areas = [
        ChartArea(
            point_names=[
                "Sofa",
                "Terraza",
                "Cocina",
                "Dormitorio (ESP)",
                "Office-Window",
                "Dormitorio",
            ],
            line_style={"color": "#50e341", "lw": 1, "alpha": 0.5, "ls": "--"},
            fill_style={"color": "#89e396", "lw": 0, "alpha": 0.2},
        )
    ]
    chart.plot()
    plot_annots_dbt_rh(chart.axes, chart_annots)
    chart.plot_legend(
        frameon=False, fontsize=15, labelspacing=0.8, markerscale=0.8
    )
    store_test_chart(chart, "test_ha_addon_psychrochart-3.svg", png=True)
