import pytest

from psychrochart import PsychroChart
from tests.conftest import RSC_EXAMPLES, store_test_chart


@pytest.mark.parametrize(
    "config, svg_dest_file, legend, ip_system",
    [
        (None, "test_default_psychrochart.svg", False, False),
        ("ashrae", "test_ashrae_psychrochart.svg", False, False),
        ("ashrae_ip", "test_ashrae_psychrochart_ip.svg", False, True),
        ("minimal", "test_minimal_psychrochart.svg", True, False),
    ],
)
def test_generate_rsc_default_charts(
    config: str | None, svg_dest_file: str, legend: bool, ip_system: bool
):
    chart = PsychroChart.create(config, use_unit_system_si=not ip_system)
    if legend:
        chart.plot_legend()

    # generate SVG as text, save PNG image
    store_test_chart(chart, svg_dest_file, svg_rsc=True)


def test_generate_rsc_splash_chart():
    """Customize a chart with some additions"""
    chart = PsychroChart.create("minimal")

    # Zones:
    zones_conf = {
        "zones": [
            {
                "zone_type": "dbt-rh",
                "style": {
                    "edgecolor": [1.0, 0.749, 0.0, 0.8],
                    "facecolor": [1.0, 0.749, 0.0, 0.2],
                    "linewidth": 2,
                    "linestyle": "--",
                },
                "points_x": [23, 28],
                "points_y": [40, 60],
                "label": "Summer",
            },
            {
                "zone_type": "dbt-rh",
                "style": {
                    "edgecolor": [0.498, 0.624, 0.8],
                    "facecolor": [0.498, 0.624, 1.0, 0.2],
                    "linewidth": 2,
                    "linestyle": "--",
                },
                "points_x": [18, 23],
                "points_y": [35, 55],
                "label": "Winter",
            },
            {
                "zone_type": "volume-rh",
                "style": {
                    "edgecolor": "k",
                    "facecolor": "#00640077",
                    "linestyle": "--",
                },
                "points_x": [0.86, 0.87],
                "points_y": [20, 80],
                "label": "V-RH zone",
            },
            {
                "zone_type": "enthalpy-rh",
                "style": {
                    "edgecolor": "k",
                    "facecolor": "#FFFF0077",
                    "linestyle": "--",
                },
                "points_x": [80, 90],
                "points_y": [40, 80],
                "label": "H-RH zone",
            },
        ]
    }
    chart.append_zones(zones_conf)

    # Plotting
    chart.plot()

    # Vertical lines
    t_min, t_opt, t_max = 16, 23, 30
    chart.plot_vertical_dry_bulb_temp_line(
        t_min,
        {"color": [0.0, 0.125, 0.376], "lw": 2, "ls": ":"},
        f"  TOO COLD ({t_min}°C)",
        ha="left",
        loc=0.0,
        fontsize=14,
    )
    chart.plot_vertical_dry_bulb_temp_line(
        t_opt, {"color": [0.475, 0.612, 0.075], "lw": 2, "ls": ":"}
    )
    chart.plot_vertical_dry_bulb_temp_line(
        t_max,
        {"color": [1.0, 0.0, 0.247], "lw": 2, "ls": ":"},
        f"TOO HOT ({t_max}°C)  ",
        ha="right",
        loc=1,
        reverse=True,
        fontsize=14,
    )

    points = {
        "exterior": {
            "label": "Exterior",
            "style": {
                "color": [0.855, 0.004, 0.278, 0.8],
                "marker": "X",
                "markersize": 15,
            },
            "xy": (31.06, 32.9),
        },
        "exterior_estimated": {
            "label": "Estimated (Weather service)",
            "style": {
                "color": [0.573, 0.106, 0.318, 0.5],
                "marker": "x",
                "markersize": 10,
            },
            "xy": (36.7, 25.0),
        },
        "interior": {
            "label": "Interior",
            "style": {
                "color": [0.592, 0.745, 0.051, 0.9],
                "marker": "o",
                "markersize": 30,
            },
            "xy": (29.42, 52.34),
        },
    }
    connectors = [
        {
            "start": "exterior",
            "end": "exterior_estimated",
            "style": {
                "color": [0.573, 0.106, 0.318, 0.7],
                "linewidth": 2,
                "linestyle": "-.",
            },
            "outline_marker_width": 50,
        },
        {
            "start": "exterior",
            "end": "interior",
            "style": {
                "color": [0.855, 0.145, 0.114, 0.8],
                "linewidth": 2,
                "linestyle": ":",
            },
            "label": "Ext->Int",
        },
    ]
    chart.plot_points_dbt_rh(points, connectors)
    chart.plot_over_saturated_zone(color_fill="#ffc1ab")

    # Legend
    chart.plot_legend(markerscale=0.5, fontsize=10, labelspacing=1.2)

    # CSS styling + SVG defs to customize and animate SVG
    svg_defs = """<linearGradient id="grad-background">
  <stop offset="0%" stop-color="#113cef" stop-opacity="0.2" />
  <stop offset="25%" stop-color="#20eecf" stop-opacity="0.2" />
  <stop offset="50%" stop-color="#eacc33" stop-opacity="0.2" />
  <stop offset="75%" stop-color="#ee6820" stop-opacity="0.2" />
  <stop offset="100%" stop-color="#ee1c09" stop-opacity="0.2" />
</linearGradient>
<linearGradient id="grad-sat">
  <stop offset="0%" stop-color="#2f2ff1"/>
  <stop offset="33%" stop-color="#EE6820"/>
  <stop offset="75%" stop-color="#ea0c4f"/>
  <stop offset="100%" stop-color="#d01cd0"/>
</linearGradient>"""

    # Save to disk
    p_svg = RSC_EXAMPLES / "chart_overlay_style_minimal.svg"
    p_svg.write_text(
        chart.make_svg(
            css_styles=RSC_EXAMPLES / "splash-chart.css",
            svg_definitions=svg_defs,
            metadata={"Date": None},
        )
    )
    # p_png = RSC_EXAMPLES / "chart_overlay_style_minimal.png"
    # chart.save(p_png, facecolor="none")
