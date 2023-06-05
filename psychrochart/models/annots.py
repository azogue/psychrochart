from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, Field, root_validator

from psychrochart.models.styles import CurveStyle, ZoneStyle
from psychrochart.models.validators import (
    check_connector_and_areas_by_point_name,
    parse_curve_arrays,
)

ConvexGroupTuple = tuple[list[str], dict[str, Any], dict[str, Any]]


class ChartPoint(BaseModel):
    """Pydantic model for single point annotation."""

    xy: tuple[float | int, float | int]
    label: str | None = Field(default=None)
    style: dict[str, Any] = Field(default_factory=dict)


class ChartSeries(BaseModel):
    """Pydantic model for data-series point array annotation."""

    # TODO fusion with PsychroCurve, + pandas ready
    x_data: np.ndarray
    y_data: np.ndarray
    style: dict[str, Any] = Field(default_factory=dict)
    label: str | None = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {np.ndarray: lambda x: x.tolist()}

    @root_validator(pre=True)
    def _parse_curve_data(cls, values):
        return parse_curve_arrays(values)


class ChartLine(BaseModel):
    """Pydantic model for a connector between 2 named points."""

    start: str
    end: str
    label: str | None = Field(default=None)
    style: CurveStyle = Field(default_factory=CurveStyle)
    outline_marker_width: int | None = Field(default=None)


class ChartArea(BaseModel):
    """Pydantic model for convex area delimited by a list of named points."""

    point_names: list[str] = Field(min_items=3)
    line_style: dict[str, Any] = Field(default_factory=dict)
    fill_style: dict[str, Any] = Field(default_factory=dict)
    # label: str | None = None

    @classmethod
    def from_tuple(cls, item: ConvexGroupTuple):
        """
        Parse area definition from old tuples.

        The syntax to add groups of given points (with more than 3 points)
        to plot a styled convex hull area was:
        ```
        interior_zones = [
            # Zone 1:
            ([point_1_name, point_2_name, point_3_name, ...],
             {"color": 'darkgreen', "lw": 0, ...},
             {"color": 'darkgreen', "lw": 0, ...}),

            # Zone 2:
            ([point_7_name, point_8_name, point_9_name, ...],
             {"color": 'darkorange', "lw": 0, ...},
             {"color": 'darkorange', "lw": 0, ...}),

            # ...
        ]
        """
        return cls.validate(
            dict(zip(["point_names", "line_style", "fill_style"], item))
        )


class ChartAnnots(BaseModel):
    """Container model for all chart annots based on overlayed data points."""

    points: dict[str, ChartPoint] = Field(default_factory=dict)
    series: dict[str, ChartSeries] = Field(default_factory=dict)
    connectors: list[ChartLine] = Field(default_factory=list)
    areas: list[ChartArea] = Field(default_factory=list)
    use_scatter: bool = Field(default=False)

    @root_validator
    def _validate_used_points(cls, values):
        return check_connector_and_areas_by_point_name(values)

    def get_point_by_name(self, key: str) -> tuple[float, float]:
        """Access coords tuple for named point (or 1st point of series)."""
        if key in self.points:
            return self.points[key].xy
        else:
            assert key in self.series
            return self.series[key].x_data[0], self.series[key].y_data[0]


class ChartZone(BaseModel):
    """Pydantic model for styled fixed areas on the psychrochart."""

    label: str | None
    zone_type: Literal["dbt-rh", "xy-points"]
    points_x: list[float]
    points_y: list[float]
    style: ZoneStyle


class ChartZones(BaseModel):
    """Container model for a list of ChartZone items."""

    zones: list[ChartZone]


# default fixed areas for winter/summer comfort zones
DEFAULT_ZONES = ChartZones(
    zones=[
        ChartZone(
            label="Summer",
            zone_type="dbt-rh",
            points_x=[23, 25],
            points_y=[45, 60],
            style=ZoneStyle(
                edgecolor=[1.0, 0.749, 0.0, 0.8],
                facecolor=[1.0, 0.749, 0.0, 0.5],
            ),
        ),
        ChartZone(
            label="Winter",
            zone_type="dbt-rh",
            points_x=[21, 23],
            points_y=[40, 50],
            style=ZoneStyle(
                edgecolor=[0.498, 0.624, 0.8],
                facecolor=[0.498, 0.624, 1.0, 0.5],
            ),
        ),
    ]
)
