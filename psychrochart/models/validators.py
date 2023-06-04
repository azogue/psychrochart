from matplotlib.colors import to_rgb
import numpy as np


def parse_color(raw_color) -> list[float]:
    """Pydantic validator for 'color' fields, stored as float values."""
    if isinstance(raw_color, str):
        return list(to_rgb(raw_color))
    return list(raw_color)


def reduce_field_abrs(values):
    """Pydantic validator for abbreviation of matplotlib style fields."""
    if "c" in values:
        values["color"] = parse_color(values.pop("c"))
    if "ls" in values:
        values["linestyle"] = values.pop("ls")
    if "lw" in values:
        values["linewidth"] = values.pop("lw")
    return values


def check_connector_and_areas_by_point_name(values):
    """Pydantic validator for ChartAnnots, removing unknown points."""
    keys_1 = set(values.get("points", {}).keys())
    keys_2 = set(values.get("series", {}).keys())
    valid_keys = keys_1 | keys_2
    values["connectors"] = [
        cn
        for cn in values["connectors"]
        if cn.start in valid_keys and cn.end in valid_keys
    ]
    valid_areas = []
    for chart_area in values["areas"]:
        point_names = [
            name for name in chart_area.point_names if name in valid_keys
        ]
        if len(point_names) >= 3:
            chart_area.point_names = point_names
            valid_areas.append(chart_area)

    values["areas"] = valid_areas
    return values


def parse_curve_arrays(values):
    """Pydantic validator to convert values into np.arrays."""
    if "x_data" in values and not isinstance(values["x_data"], np.ndarray):
        values["x_data"] = np.array(values["x_data"])
    if "y_data" in values and not isinstance(values["y_data"], np.ndarray):
        values["y_data"] = np.array(values["y_data"])
    return values
