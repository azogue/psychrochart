from typing import Any

import numpy as np
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    model_validator,
)

from psychrochart.models.styles import CurveStyle
from psychrochart.models.validators import (
    check_connector_and_areas_by_point_name,
    parse_curve_arrays,
)

ConvexGroupTuple = tuple[list[str], dict[str, Any], dict[str, Any]]


class ChartPoint(BaseModel):
    """Input model for single point annotations."""

    xy: tuple[float | int, float | int]
    label: str | None = Field(default=None)
    style: dict[str, Any] = Field(default_factory=dict)


class ChartSeries(BaseModel):
    """Input model for data-series point array annotation."""

    x_data: np.ndarray
    y_data: np.ndarray
    style: dict[str, Any] = Field(default_factory=dict)
    label: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("x_data", "y_data")
    def _serialize_arrays(self, values: np.ndarray, _info):
        return values.tolist()

    @model_validator(mode="before")
    @classmethod
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

    point_names: list[str] = Field(min_length=3)
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
        return cls.model_validate(
            dict(zip(["point_names", "line_style", "fill_style"], item))
        )


class ChartAnnots(BaseModel):
    """Container model for all chart annots based on overlayed data points."""

    points: dict[str, ChartPoint] = Field(default_factory=dict)
    series: dict[str, ChartSeries] = Field(default_factory=dict)
    connectors: list[ChartLine] = Field(default_factory=list)
    areas: list[ChartArea] = Field(default_factory=list)
    use_scatter: bool = Field(default=False)

    @model_validator(mode="before")
    @classmethod
    def _validate_used_points(cls, values):
        return check_connector_and_areas_by_point_name(values)

    def get_point_by_name(self, key: str) -> tuple[float, float]:
        """Access coords tuple for named point (or 1st point of series)."""
        if key in self.points:
            return self.points[key].xy
        else:
            assert key in self.series
            return self.series[key].x_data[0], self.series[key].y_data[0]
