import json
from pathlib import Path
from typing import Any

from pydantic import parse_obj_as
import pytest

from psychrochart.models.annots import ChartAnnots, ChartArea, ChartPoint
from psychrochart.models.config import (
    ChartConfig,
    ChartZone,
    ChartZones,
    DEFAULT_ZONES,
)
from psychrochart.models.parsers import (
    DEFAULT_CHART_CONFIG_FILE,
    load_extra_annots,
    load_points_dbt_rh,
    obj_loader,
    PATH_STYLES,
)
from psychrochart.models.styles import CurveStyle
from psychrochart.process_logic import set_unit_system


def test_default_config():
    default_config = ChartConfig()
    config = ChartConfig.parse_file(DEFAULT_CHART_CONFIG_FILE)
    assert default_config == config

    simple_repr = (
        config.json(indent=2)
        .replace(".0,", ",")
        .replace(".0\n", "\n")
        .replace(".0]", "]")
    )
    stored_data = json.loads(
        Path(DEFAULT_CHART_CONFIG_FILE).read_text("UTF-8")
    )
    assert json.dumps(stored_data, indent=2) == simple_repr


def _update_config(
    old_conf: dict[str, Any], new_conf: dict[str, Any], recurs_idx: int = 0
) -> dict[str, Any]:
    """Update a dict recursively."""
    assert recurs_idx < 3
    if old_conf is None:
        return new_conf
    for key, value in old_conf.items():
        if key in new_conf:
            if isinstance(value, dict) and isinstance(new_conf[key], dict):
                new_value = _update_config(
                    old_conf[key], new_conf[key], recurs_idx + 1
                )
            else:
                new_value = new_conf[key]
            old_conf[key] = new_value
    if recurs_idx > 0:
        old_conf.update(
            {
                key: new_conf[key]
                for key in filter(lambda x: x not in old_conf, new_conf)
            }
        )
    return old_conf


@pytest.mark.parametrize(
    "style_file",
    (
        "ashrae_chart_style.json",
        "ashrae_ip_chart_style.json",
        "default_chart_config.json",
        "interior_chart_style.json",
        "minimal_chart_style.json",
    ),
)
def test_config_presets(style_file: str):
    p_file = PATH_STYLES / style_file
    assert p_file.exists()
    parsed_config = ChartConfig.parse_file(p_file)
    # print(p_file.read_text())
    # old method, without pydantic
    stored_data = json.loads(p_file.read_text("UTF-8"))

    old_config_data = _update_config(ChartConfig().dict(), stored_data)
    old_config = ChartConfig.validate(old_config_data)

    # check equivalency
    assert parsed_config == old_config
    assert parsed_config.json(indent=2).replace(".0,", ",").replace(
        ".0\n", "\n"
    ).replace(".0]", "]") == old_config.json(indent=2).replace(
        ".0,", ","
    ).replace(
        ".0\n", "\n"
    ).replace(
        ".0]", "]"
    )


def test_zone_presets():
    p_file = PATH_STYLES / "default_comfort_zones.json"
    assert p_file.exists()
    parsed_zones = ChartZones.parse_file(p_file)
    assert parsed_zones == DEFAULT_ZONES


def test_styles_with_extra_fields():
    style_extra = CurveStyle(
        color=[0.3, 0.3, 0.3], linewidth=2, linestyle="-", marker="o"
    )
    assert CurveStyle.validate(style_extra.dict()) == style_extra
    assert style_extra.marker == "o"


def test_style_parsing():
    raw_style = {"c": "orange", "lw": 5, "ls": ":"}
    style = obj_loader(CurveStyle, raw_style)
    assert isinstance(style, CurveStyle)
    assert isinstance(style.color, list)
    assert style.linestyle == ":"
    assert not hasattr(style, "ls")
    assert style.linewidth == 5
    assert not hasattr(style, "lw")
    assert style.linewidth == 5
    assert not hasattr(style, "c")

    style = CurveStyle(**raw_style)
    assert isinstance(style, CurveStyle)
    assert isinstance(style.color, list)
    assert style.linestyle == ":"
    assert not hasattr(style, "ls")
    assert style.linewidth == 5
    assert not hasattr(style, "lw")
    assert not hasattr(style, "c")


def test_chart_zone_definition():
    style = {
        "style": {
            "edgecolor": "red",
            "facecolor": "blue",
            "linewidth": 1,
            "linestyle": ":",
        }
    }

    z1 = {
        "points_x": [23.0, 25.0, 24.0],
        "points_y": [45.0, 60.0, 25.0],
        **style,
    }
    zone1 = ChartZone.validate(z1)
    assert zone1.zone_type == "xy-points"
    assert zone1.label is None

    # invalid number of points
    with pytest.raises(ValueError):
        ChartZone.validate({"points_x": [], "points_y": [], **style})
    with pytest.raises(ValueError):
        ChartZone.validate({"points_x": [25.0], "points_y": [25.0], **style})
    with pytest.raises(ValueError):
        ChartZone.validate(
            {"points_x": [25.0, 25.0], "points_y": [25.0, 25.0, 25.0], **style}
        )

    # dbt-rh zones have 2 points: (dbt-min, RH-min),  (dbt-max, RH-max)
    z1["zone_type"] = "dbt-rh"
    with pytest.raises(ValueError):
        ChartZone.validate(z1)

    z1["points_x"] = [23.0, 25.0]
    z1["points_y"] = [45.0, 60.0]
    zone2 = ChartZone.validate(z1)
    assert zone2.zone_type == "dbt-rh"
    assert zone2.label is None


def test_chart_area_schema():
    raw_areas_as_dict = [
        # Zone 1:
        {
            "point_names": ["point_1_name", "point_2_name", "point_3_name"],
            "line_style": {"color": "darkgreen", "lw": 0},
            "fill_style": {"color": "darkgreen", "lw": 0},
        },
        # Zone 2:
        {
            "point_names": ["point_7_name", "point_8_name", "point_9_name"],
            "line_style": {"color": "darkorange", "lw": 0},
            "fill_style": {"color": "darkorange", "lw": 0},
        },
    ]
    a1, a2 = parse_obj_as(list[ChartArea], raw_areas_as_dict)
    assert len(set(a1.point_names + a2.point_names)) == 6
    assert a1.fill_style == a1.line_style
    assert a2.fill_style == a2.line_style
    assert a1 != a2

    # old syntax
    raw_areas_as_tuple = [
        # Zone 1:
        (
            ["point_1_name", "point_2_name", "point_3_name"],  # list of points
            {"color": "darkgreen", "lw": 0},  # line style
            {"color": "darkgreen", "lw": 0},  # filling style
        ),
        # Zone 2:
        (
            ["point_7_name", "point_8_name", "point_9_name"],  # list of points
            {"color": "darkorange", "lw": 0},  # line style
            {"color": "darkorange", "lw": 0},  # filling style
        ),
    ]
    a1_bis, a2_bis = [ChartArea.from_tuple(i) for i in raw_areas_as_tuple]
    assert a1 == a1_bis
    assert a2 == a2_bis


def test_chart_annots_schema():
    raw_annots = {
        "points": {
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
            "other": {"xy": (29.42, 52.34)},
        },
        # "series": {},
        "connectors": [
            {
                "start": "exterior",
                "end": "exterior_estimated",
                "label": "Process 1",
                "style": {
                    "color": [0.573, 0.106, 0.318, 0.7],
                    "linewidth": 2.0,
                    "linestyle": "-.",
                },
            },
            {
                "start": "exterior",
                "end": "interior",
                "label": "Process 2",
                "style": {
                    "color": [0.855, 0.145, 0.114, 0.8],
                    "linewidth": 2.0,
                    "linestyle": ":",
                },
            },
        ],
        # "areas": [],
        # "use_scatter": False,
    }
    example_annots = ChartAnnots.validate(raw_annots)
    assert example_annots.dict(exclude_unset=True) == raw_annots
    assert len(example_annots.points) == 4
    assert len(example_annots.connectors) == 2


def test_chart_annots_definition():
    # empty by default
    assert (
        not ChartAnnots().points
        and not ChartAnnots().series
        and not ChartAnnots().connectors
        and not ChartAnnots().areas
    )

    # minimal 1-point annot:
    annot_1 = ChartAnnots(points={"p1": {"xy": [3, 4]}})
    # annot_1 = ChartAnnots(points={"p1": {"x_data": [3], "y_data": [4]}})
    assert isinstance(annot_1.points["p1"], ChartPoint)
    assert not annot_1.points["p1"].style
    assert not annot_1.points["p1"].label
    assert annot_1.points["p1"].xy == (3.0, 4.0)

    # cannot add lines if start/end points do not exist
    annot_2 = ChartAnnots(
        points={"p1": {"xy": [3, 4]}, "p2": {"xy": [5, 6]}},
        connectors=[{"start": "p1", "end": "p2", "style": {"lw": 7}}],
    )
    # print(annot_2.json(indent=2))
    assert annot_2.connectors[0].style.linewidth == 7
    assert annot_2.connectors[0].label is None

    # cannot add lines if start/end points do not exist
    annot_3 = ChartAnnots(
        points={"p1": {"xy": [3, 4]}, "p2": {"xy": [5, 6]}},
        connectors=[{"start": "p1", "end": "p7"}],
    )
    assert len(annot_3.points) == 2
    assert not annot_3.connectors

    # areas reduced to available points/series
    annot_4 = ChartAnnots(
        points={"p1": {"xy": [3, 4]}, "p2": {"xy": [5, 6]}},
        series={"p3": {"x_data": [3, 4], "y_data": [4, 5]}},
        areas=[
            {
                "point_names": ["p1", "p2", "p3", "p4"],
                "line_style": {"color": "green", "lw": 0},
                "fill_style": {"color": "darkgreen"},
            },
            {
                "point_names": ["p7", "p8", "p4"],
                "line_style": {"color": "orange", "lw": 0},
                "fill_style": {"color": "darkorange"},
            },
        ],
    )
    assert len(annot_4.points) == 2
    assert len(annot_4.series) == 1
    assert len(annot_4.areas) == 1
    assert len(annot_4.areas[0].point_names) == 3


def test_parse_points():
    set_unit_system()
    points = {
        "pt_simple_1": (36.7, 25.0),
        "pt_simple_2": [29.42, 52.34],
        "pt_detailed": {
            "label": "Exterior",
            "style": {
                "color": [0.855, 0.004, 0.278, 0.8],
                "marker": "X",
                "markersize": 15,
            },
            "xy": (31.06, 32.9),
        },
        "pt_mult": {"xy": ([31.06, 32.9], [36.7, 25.0])},
        "pt_mult_detailed": {
            "xy": ([31.06, 32.9], [36.7, 25.0]),
            "style": {"color": "red", "markersize": 15},
        },
        "bad_entry": 29.42,
    }
    points_plot, series_plot = load_points_dbt_rh(points, pressure=101325.0)
    assert len(points_plot) == 3
    assert len(series_plot) == 2


def test_parse_areas():
    set_unit_system()
    points = {
        "exterior": (31.06, 32.9),
        "exterior_estimated": (36.7, 25.0),
        "interior": (29.42, 52.34),
    }

    convex_groups_bad = [
        (["exterior", "interior"], {}, {}),
    ]
    with pytest.raises(ValueError):
        load_extra_annots([], convex_groups_bad)
    convex_groups_bad_2 = [
        {
            "point_names": ["exterior", "interior"],
            "line_style": {"color": "green", "lw": 0},
            "fill_style": {"color": "darkgreen"},
        }
    ]
    with pytest.raises(ValueError):
        load_extra_annots([], convex_groups_bad_2)

    convex_groups = [
        (["exterior", "exterior_estimated", "interior"], {}, {}),
    ]
    data_points, data_series = load_points_dbt_rh(points, 101325.0)
    data_lines, data_areas = load_extra_annots([], convex_groups)
    annots = ChartAnnots(
        points=data_points,
        series=data_series,
        connectors=data_lines,
        areas=data_areas,
    )
    assert annots.points
    assert not annots.series
    assert annots.areas
    assert not annots.connectors
