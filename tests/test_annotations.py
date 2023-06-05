from psychrochart.agg import PsychroChart
from tests.conftest import TEST_BASEDIR

_TEST_POINTS = {
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
_TEST_SERIES = {
    "evolution-1": {
        "xy": ([24.2, 23.6, 22.9, 21.5], [70.3, 70.5, 71.7, 75.6]),
        "label": "Day evolution",
        "style": {
            "color": [0.855, 0.004, 0.278, 0.8],
            "marker": "o",
            "markersize": 2,
            "linewidth": 1,
        },
    },
    "evolution-2": {
        "xy": ([21.2, 20.6, 19.9, 18.5], [50.3, 50.5, 51.7, 55.6]),
        "style": {
            "color": [0.255, 0.004, 0.278, 0.7],
            "linewidth": 2,
        },
    },
}
_TEST_CONNECTORS = [
    {
        "start": "exterior",
        "end": "exterior_estimated",
        "style": {
            "color": [0.573, 0.106, 0.318, 0.7],
            "linewidth": 2,
            "linestyle": "-.",
        },
        # "outline_marker_width": 50,
    },
    {
        "start": "exterior",
        "end": "interior",
        "style": {
            "color": [0.855, 0.145, 0.114, 0.8],
            "linewidth": 2,
            "linestyle": ":",
        },
        # "outline_marker_width": 50,
    },
]
_TEST_ZONES = {
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
            "label": "Labeled zone",
        },
    ]
}
_TEST_AREA = {
    "point_names": [
        "exterior",
        "exterior_estimated",
        "interior",
        "lost_sensor",
        "evolution-1",
        "evolution-2",
    ],
    "fill_style": {
        "color": [0.498, 0.624, 1.0, 0.2],
        "linewidth": 1,
    },
    "line_style": {
        "color": [0.498, 0.624, 0.0, 0.2],
        "linewidth": 1,
        "linestyle": ":",
    },
}


def _make_base_chart():
    chart = PsychroChart.create("minimal")
    chart.append_zones(_TEST_ZONES)
    chart.plot()

    # add vertical lines
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
    return chart


def _store_chart(
    chart: PsychroChart, chart_name: str, add_legend: bool = True
):
    if add_legend:
        chart.plot_legend(
            markerscale=0.7, frameon=False, fontsize=10, labelspacing=1.2
        )
    chart.save(TEST_BASEDIR / chart_name)


def test_base_chart():
    chart = _make_base_chart()
    _store_chart(chart, "testchart_overlay_base.png", add_legend=False)


def test_overlay_single_points():
    chart = _make_base_chart()
    chart.plot_points_dbt_rh(_TEST_POINTS)
    _store_chart(chart, "testchart_plot_points.png")

    chart = _make_base_chart()
    chart.plot_points_dbt_rh(
        _TEST_POINTS,
        scatter_style={"s": 300, "alpha": 0.7, "color": "darkorange"},
    )
    _store_chart(chart, "testchart_scatter_points.png")


def test_connected_points():
    chart = _make_base_chart()
    chart.plot_points_dbt_rh(_TEST_POINTS, _TEST_CONNECTORS)
    _store_chart(chart, "testchart_connected_points.png", add_legend=False)


def test_marked_connected_points():
    chart = _make_base_chart()
    connectors = [item.copy() for item in _TEST_CONNECTORS]
    connectors[0]["outline_marker_width"] = 50
    connectors[1]["outline_marker_width"] = 50
    chart.plot_points_dbt_rh(_TEST_POINTS, connectors)
    _store_chart(chart, "testchart_marked_connected_points.png")


def test_connected_array():
    chart = _make_base_chart()
    chart.plot_points_dbt_rh(_TEST_SERIES)
    _store_chart(chart, "testchart_connected_array.png", add_legend=False)


def test_convex_hull():
    chart = _make_base_chart()

    chart.plot_points_dbt_rh(
        points=_TEST_POINTS | _TEST_SERIES,
        convex_groups=[_TEST_AREA],
    )
    _store_chart(chart, "testchart_convex_hull.png", add_legend=False)


def test_all_annots():
    chart = _make_base_chart()
    chart.plot_points_dbt_rh(
        points=_TEST_POINTS | _TEST_SERIES,
        connectors=[_TEST_CONNECTORS[0] | {"outline_marker_width": 25}],
        convex_groups=[_TEST_AREA],
    )
    _store_chart(chart, "testchart_all_annots.png")
