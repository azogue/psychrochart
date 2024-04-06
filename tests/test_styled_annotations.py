from psychrochart import PsychroChart
from tests.conftest import store_test_chart


def test_styled_psychrochart_with_negative_h_labels_loc():
    """Test styled annotations, also using negative constant_h_labels_loc."""
    altitude = 200
    title = f"Carta psicrométrica - Altitude: {altitude} m"
    custom_style = {
        "figure": {
            "figsize": [9.5, 6],
            "fontsize": 8,
            "title": title,
            "x_label": "TEMPERATURA BULBO ÚMIDO, $°C$",
            "y_label": "UMIDADE ABSOLUTA $w, g_w / kg_{da}$",
            "x_axis": {"color": [0, 0, 0], "linewidth": 1, "linestyle": "-"},
            "x_axis_labels": {"color": [0, 0, 0], "fontsize": 6},
            "x_axis_ticks": {"direction": "out", "color": [0, 0, 0]},
            "y_axis": {"color": [0, 0, 0], "linewidth": 1, "linestyle": "-"},
            "y_axis_labels": {"color": [0, 0, 0], "fontsize": 6},
            "y_axis_ticks": {"direction": "out", "color": [0, 0, 0]},
            "partial_axis": False,
            "position": [0.025, 0.075, 0.925, 0.875],
        },
        "limits": {
            "range_temp_c": [0, 50],
            "range_humidity_g_kg": [0, 30],
            "altitude_m": altitude,
            "step_temp": 1,
        },
        "saturation": {"color": [0, 0, 0], "linewidth": 1.5, "linestyle": "-"},
        "constant_rh": {
            "color": [0, 0, 0],
            "linewidth": 0.75,
            "linestyle": "-",
        },
        "constant_v": {
            "color": [0, 0, 0],
            "linewidth": 0.25,
            "linestyle": "-",
        },
        "constant_h": {"color": [0, 0, 0], "linewidth": 0.5, "linestyle": "-"},
        "constant_wet_temp": {
            "color": [0, 0, 0],
            "linewidth": 0.75,
            "linestyle": "--",
        },
        "constant_dry_temp": {
            "color": [0, 0, 0, 0.5],
            "linewidth": 0.25,
            "linestyle": "-",
        },
        "constant_humidity": {
            "color": [0, 0, 0, 0.5],
            "linewidth": 0.25,
            "linestyle": "-",
        },
        "chart_params": {
            "with_constant_rh": True,
            "constant_rh_curves": [10, 20, 30, 40, 50, 60, 70, 80, 90],
            "constant_rh_labels": [10, 20, 30, 40, 50],
            "with_constant_v": True,
            "constant_v_step": 0.01,
            "range_vol_m3_kg": [0.78, 0.96],
            "constant_v_labels": [0.8, 0.85, 0.9],
            "with_constant_h": True,
            "constant_h_step": 10,
            "constant_h_labels": [20, 30, 40, 50, 60, 70, 80, 90, 100],
            "range_h": [10, 130],
            "constant_h_labels_loc": -0.06,
            "with_constant_wet_temp": True,
            "constant_wet_temp_step": 1,
            "range_wet_temp": [-10, 35],
            "constant_wet_temp_labels": [0, 5, 10, 15, 20, 25, 30],
            "with_constant_dry_temp": True,
            "constant_temp_step": 1,
            "with_constant_humidity": True,
            "constant_humid_step": 0.5,
            "with_zones": False,
        },
        "constant_v_annotation": {
            "color": [0.2, 0.2, 0.2],
            "fontsize": 7,
            "bbox": {
                "boxstyle": "square,pad=-0.2",
                "color": [1, 1, 1, 0.9],
                "lw": 0.5,
            },
        },
        "constant_h_annotation": {
            "color": [0.2, 0.2, 0.2],
            "fontsize": 6,
            "bbox": {
                "boxstyle": "square,pad=-0.1",
                "color": [1, 1, 1, 0.9],
                "lw": 0.5,
            },
        },
        "constant_wet_temp_annotation": {
            "color": [0.2, 0.2, 0.2],
            "fontsize": 7,
            "bbox": {
                "boxstyle": "square,pad=0",
                "color": [1, 1, 1, 0.9],
                "lw": 0.5,
            },
        },
        "constant_rh_annotation": {
            "color": [0.2, 0.2, 0.2],
            "fontsize": 7,
            "bbox": {
                "boxstyle": "square,pad=0",
                "color": [1, 1, 1, 0.9],
                "lw": 0.5,
            },
        },
    }

    chart = PsychroChart.create(custom_style)
    target_zone = {
        "zones": [
            {
                "zone_type": "dbt-rh",
                "style": {
                    "edgecolor": [1.0, 0.749, 0.0, 0.2],
                    "facecolor": [1.0, 0.749, 0.0, 0.2],
                    "fill": True,
                    "linewidth": 1,
                    "linestyle": "--",
                },
                "points_x": [23, 28],
                "points_y": [40, 60],
                "label": "Target",
                "annotation_style": {"color": [0.3, 0.3, 0.3], "fontsize": 10},
            }
        ]
    }
    chart.append_zones(target_zone)

    chart.plot()
    store_test_chart(chart, "chart_styled_annotations.svg", png=True)
