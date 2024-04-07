from pathlib import Path
from typing import Any, Iterable, Type, TypeVar

import numpy as np
from pydantic import BaseModel, TypeAdapter

from psychrochart.chartdata import gen_points_in_constant_relative_humidity
from psychrochart.models.annots import (
    ChartArea,
    ChartLine,
    ChartPoint,
    ChartSeries,
    ConvexGroupTuple,
)
from psychrochart.models.config import ChartConfig, ChartZones, DEFAULT_ZONES

PATH_STYLES = Path(__file__).absolute().parents[1] / "chart_styles"
DEFAULT_CHART_CONFIG_FILE = PATH_STYLES / "default_chart_config.json"
ASHRAE_CHART_CONFIG_FILE = PATH_STYLES / "ashrae_chart_style.json"
ASHRAE_IP_CHART_CONFIG_FILE = PATH_STYLES / "ashrae_ip_chart_style.json"
INTERIOR_CHART_CONFIG_FILE = PATH_STYLES / "interior_chart_style.json"
MINIMAL_CHART_CONFIG_FILE = PATH_STYLES / "minimal_chart_style.json"
DEFAULT_ZONES_FILE = PATH_STYLES / "default_comfort_zones.json"

STYLES = {
    "ashrae": ASHRAE_CHART_CONFIG_FILE,
    "ashrae_ip": ASHRAE_IP_CHART_CONFIG_FILE,
    "default": DEFAULT_CHART_CONFIG_FILE,
    "interior": INTERIOR_CHART_CONFIG_FILE,
    "minimal": MINIMAL_CHART_CONFIG_FILE,
}

T = TypeVar("T", bound=BaseModel)


def obj_loader(
    data_cls: Type[T],
    data: T | dict[str, Any] | str | Path | None = None,
    default_obj: T | None = None,
) -> T:
    """Load pydantic model from disk, or raw, with optional defaults."""
    if data is None:
        return default_obj if default_obj is not None else data_cls()
    if isinstance(data, data_cls):
        return data
    if isinstance(data, str) and data in STYLES:
        return data_cls.model_validate_json(STYLES[data].read_text())
    if isinstance(data, (str, Path)):
        return data_cls.model_validate_json(Path(data).read_text())
    assert isinstance(data, dict)
    return data_cls(**data)


def load_config(
    config: ChartConfig | dict[str, Any] | Path | str | None = None,
) -> ChartConfig:
    """Load the plot params for the psychrometric chart."""
    return obj_loader(ChartConfig, config)


def load_zones(
    zones: ChartZones | dict[str, Any] | str | None = None,
) -> ChartZones:  # pragma: no cover
    """Load a zones JSON file to overlay in the psychrometric chart."""
    return obj_loader(ChartZones, zones, default_obj=DEFAULT_ZONES)


def load_points_dbt_rh(
    points: dict[str, Any],
    pressure: float,
    scatter_style: dict[str, Any] | None = None,
) -> tuple[dict[str, ChartPoint], dict[str, ChartSeries]]:
    """Load chart single-point + point-array annots with multiple syntaxes."""
    points_plot: dict[str, ChartPoint] = {}
    series_plot: dict[str, ChartSeries] = {}
    default_style = {
        "marker": "o",
        "markersize": 10,
        "color": [1.0, 0.8, 0.1, 0.8],
        "linewidth": 0,
    }
    if scatter_style is not None:
        default_style = scatter_style
    for point_name, point_data in points.items():
        label: str | None = None
        plot_params = default_style.copy()
        if isinstance(point_data, dict) and isinstance(
            point_data["xy"][0], Iterable
        ):
            # arrays with 'xy' notation inside dict
            temperatures, rh_data = point_data["xy"]
            plot_params.update(point_data.get("style", {}))
            label = point_data.get("label")

            w_g_ka = gen_points_in_constant_relative_humidity(
                temperatures, rh_data, pressure
            )
            series_plot[point_name] = ChartSeries(
                x_data=temperatures,
                y_data=w_g_ka,
                style=plot_params,
                label=label,
            )
        elif isinstance(point_data, dict):
            # single points with 'xy' notation inside dict
            x_data, y_data = point_data["xy"]
            plot_params.update(point_data.get("style", {}))
            label = point_data.get("label")

            w_g_ka = gen_points_in_constant_relative_humidity(
                [x_data], y_data, pressure
            )
            points_plot[point_name] = ChartPoint(
                xy=(x_data, w_g_ka[0]),
                style=plot_params,
                label=label,
            )
        elif isinstance(point_data, (list, tuple)):
            # simple labeled data
            x_data = point_data[0]
            y_data = point_data[1]
            if isinstance(x_data, Iterable):
                # simple labeled array
                temperatures = np.array(x_data)
                w_g_ka = gen_points_in_constant_relative_humidity(
                    temperatures, y_data, pressure
                )
                series_plot[point_name] = ChartSeries(
                    x_data=temperatures,
                    y_data=w_g_ka,
                    style=plot_params,
                    label=label,
                )
            else:
                # simple labeled point
                w_g_ka = gen_points_in_constant_relative_humidity(
                    [x_data], y_data, pressure
                )
                points_plot[point_name] = ChartPoint(
                    xy=(x_data, w_g_ka[0]),
                    style=plot_params,
                    label=label,
                )

    return points_plot, series_plot


def load_extra_annots(
    connectors: list[dict[str, Any]] | None = None,
    convex_groups: list[dict[str, Any]] | list[ConvexGroupTuple] | None = None,
) -> tuple[list[ChartLine], list[ChartArea]]:
    """Load chart lines + convex groups annotations."""
    data_connectors = TypeAdapter(list[ChartLine]).validate_python(
        connectors or []
    )
    data_areas = []
    if convex_groups and isinstance(convex_groups[0], dict):
        data_areas = TypeAdapter(list[ChartArea]).validate_python(
            convex_groups
        )
    elif convex_groups and isinstance(convex_groups[0], tuple):
        data_areas = [
            ChartArea.from_tuple(it)  # type: ignore
            for it in convex_groups
        ]
    return data_connectors, data_areas
