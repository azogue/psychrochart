from typing import Literal

from pydantic import Field, model_validator

from psychrochart.models.base import BaseConfig
from psychrochart.models.styles import (
    AnnotationStyle,
    CurveStyle,
    LabelStyle,
    TickStyle,
    ZoneStyle,
)

_DEFAULT_RANGE_VOL_M3_KG = (0.78, 0.98)
_DEFAULT_RANGE_ENTALPHY = (5, 155)
_DEFAULT_RANGE_WET_TEMP = (-10, 40)
_DEFAULT_POSITION = [0.025, 0.075, 0.925, 0.875]

_DEFAULT_RH_CURVES = [10, 20, 30, 40, 45, 50, 55, 60, 70, 80, 90]
_DEFAULT_CONSTANT_RH_LABELS = [20, 30, 40, 50, 60, 70, 80]
_DEFAULT_CONSTANT_V_LABELS = [0.8, 0.9, 0.96]
_DEFAULT_CONSTANT_H_LABELS = [5.0, 25.0, 50.0, 75.0, 100.0, 125.0]
_DEFAULT_CONSTANT_WET_TEMP_LABELS = [
    0.0,
    5.0,
    10.0,
    15.0,
    20.0,
    25.0,
    30.0,
    35.0,
]

_DEFAULT_X_AXIS = CurveStyle(color=[0.2, 0.2, 0.2], linewidth=2)
_DEFAULT_Y_AXIS = CurveStyle(color=[0.3, 0.3, 0.3], linewidth=2)
_DEFAULT_X_AXIS_LABELS = LabelStyle(color=[0.2, 0.2, 0.2], fontsize=9)
_DEFAULT_Y_AXIS_LABELS = LabelStyle(color=[0.3, 0.3, 0.3], fontsize=8)
_DEFAULT_X_AXIS_TICKS = TickStyle(color=[0.2, 0.2, 0.2], direction="out")
_DEFAULT_Y_AXIS_TICKS = TickStyle(color=[0.3, 0.3, 0.3], direction="out")
_DEFAULT_STYLE_SAT = CurveStyle(color=[0.855, 0.004, 0.278], linewidth=3)
_DEFAULT_STYLE_RH = CurveStyle(color=[0.0, 0.498, 1.0], linestyle="-.")
_DEFAULT_STYLE_V = CurveStyle(color=[0.0, 0.502, 0.337], linestyle="--")
_DEFAULT_STYLE_H = CurveStyle(color=[0.251, 0.0, 0.502], linestyle="--")
_DEFAULT_STYLE_WET_TEMP = CurveStyle(color=[0.498, 0.875, 1.0], linestyle="-.")
_DEFAULT_STYLE_DRY_TEMP = CurveStyle(
    color=[0.855, 0.145, 0.114], linewidth=0.75, linestyle=":"
)
_DEFAULT_STYLE_HUMID = CurveStyle(
    color=[0.0, 0.125, 0.376], linewidth=0.75, linestyle=":"
)
_DEFAULT_STYLE_CURVES_ANNOTATION = AnnotationStyle(fontsize=10)

ZoneKind = Literal[
    "dbt-rh", "xy-points", "enthalpy-rh", "volume-rh", "dbt-wmax"
]


class ChartFigure(BaseConfig):
    """Psychrochart settings for matplotlib Figure."""

    figsize: tuple[float, float] = Field(default=(16, 9))
    dpi: int = Field(default=150)
    fontsize: int = Field(default=10)
    title: str | None = Field(default="Psychrometric Chart")
    x_label: str | None = Field(default="Dry-bulb temperature, $°C$")
    y_label: str | None = Field(default="Humidity ratio $w, g_w / kg_{da}$")

    x_axis: CurveStyle = Field(default=_DEFAULT_X_AXIS)
    x_axis_labels: LabelStyle = Field(default=_DEFAULT_X_AXIS_LABELS)
    y_axis: CurveStyle = Field(default=_DEFAULT_Y_AXIS)
    y_axis_labels: LabelStyle = Field(default=_DEFAULT_Y_AXIS_LABELS)
    x_axis_ticks: TickStyle | None = Field(default=_DEFAULT_X_AXIS_TICKS)
    y_axis_ticks: TickStyle | None = Field(default=_DEFAULT_Y_AXIS_TICKS)

    partial_axis: bool = Field(default=True)
    position: list[float] = Field(
        default_factory=lambda: list(_DEFAULT_POSITION)
    )


class ChartLimits(BaseConfig):
    """Psychrochart temperature + humidity + pressure limits."""

    range_temp_c: tuple[float, float] = Field(default=(0, 50))
    range_humidity_g_kg: tuple[float, float] = Field(default=(0, 40))
    altitude_m: int = Field(default=0)
    pressure_kpa: float | None = Field(default=None)
    step_temp: float = Field(default=1)


class ChartZone(BaseConfig):
    """Pydantic model for styled fixed areas on the psychrochart."""

    points_x: list[float]
    points_y: list[float]
    label: str | None = Field(default=None)
    zone_type: ZoneKind = Field(default="xy-points")
    style: ZoneStyle
    annotation_style: AnnotationStyle = Field(default_factory=AnnotationStyle)

    @model_validator(mode="after")
    def _validate_zone_definition(self):
        shape = len(self.points_x), len(self.points_y)
        if shape[0] < 2 or shape[1] < 2 or shape[0] != shape[1]:
            raise ValueError(f"Invalid shape: {shape}")
        if self.zone_type != "xy-points" and (
            shape != (2, 2)
            or (self.points_x[1] < self.points_x[0])
            or (self.points_y[1] < self.points_y[0])
        ):
            raise ValueError(f"Invalid shape for {self.zone_type}: {shape}")
        return self


class ChartZones(BaseConfig):
    """Container model for a list of ChartZone items."""

    zones: list[ChartZone] = Field(default_factory=list)


class ChartParams(BaseConfig):
    """Psychrochart plotting parameters."""

    with_constant_rh: bool = Field(default=True)
    constant_rh_label: str | None = Field(default="Constant relative humidity")
    constant_rh_curves: list[int] = Field(default=_DEFAULT_RH_CURVES)
    constant_rh_labels: list[int] = Field(default=_DEFAULT_CONSTANT_RH_LABELS)
    constant_rh_labels_loc: float = Field(default=0.85)

    with_constant_v: bool = Field(default=True)
    constant_v_label: str | None = Field(default="Constant specific volume")
    constant_v_step: float = Field(default=0.02)
    range_vol_m3_kg: tuple[float, float] = Field(
        default=_DEFAULT_RANGE_VOL_M3_KG
    )
    constant_v_labels: list[float] = Field(
        default_factory=_DEFAULT_CONSTANT_V_LABELS.copy
    )
    constant_v_labels_loc: float = Field(default=1.0)

    with_constant_h: bool = Field(default=True)
    constant_h_label: str | None = Field(default="Constant enthalpy")
    constant_h_step: float = Field(default=5)
    range_h: tuple[float, float] = Field(default=_DEFAULT_RANGE_ENTALPHY)
    constant_h_labels: list[float] = Field(
        default_factory=_DEFAULT_CONSTANT_H_LABELS.copy
    )
    constant_h_labels_loc: float = Field(default=1)

    with_constant_wet_temp: bool = Field(default=True)
    constant_wet_temp_label: str | None = Field(
        default="Constant wet bulb temperature"
    )
    constant_wet_temp_step: float = Field(default=5)
    range_wet_temp: tuple[float, float] = Field(
        default=_DEFAULT_RANGE_WET_TEMP
    )
    constant_wet_temp_labels: list[float] = Field(
        default_factory=_DEFAULT_CONSTANT_WET_TEMP_LABELS.copy
    )
    constant_wet_temp_labels_loc: float = Field(default=0.05)

    with_constant_dry_temp: bool = Field(default=True)
    constant_temp_label: str | None = Field(default="Dry bulb temperature")
    constant_temp_step: float = Field(default=1)
    constant_temp_label_step: float = Field(default=5)
    constant_temp_label_include_limits: bool = Field(default=True)
    with_constant_humidity: bool = Field(default=True)
    constant_humid_label: str | None = Field(default="Absolute humidity")
    constant_humid_step: float = Field(default=1)
    constant_humid_label_step: float = Field(default=2)
    constant_humid_label_include_limits: bool = Field(default=True)

    with_zones: bool = Field(default=True)
    zones: list[ChartZone] = Field(default_factory=list)


class ChartConfig(BaseConfig):
    """
    Psychrochart configuration model.

    Includes:
    * matplotlib figure settings and styling
    * chart limits
    * plotting parameters
    * plot styling for each kind of psychrometric curve
    """

    figure: ChartFigure = Field(default_factory=ChartFigure)
    limits: ChartLimits = Field(default_factory=ChartLimits)

    saturation: CurveStyle = Field(default=_DEFAULT_STYLE_SAT)
    constant_rh: CurveStyle = Field(default=_DEFAULT_STYLE_RH)
    constant_v: CurveStyle = Field(default=_DEFAULT_STYLE_V)
    constant_h: CurveStyle = Field(default=_DEFAULT_STYLE_H)
    constant_wet_temp: CurveStyle = Field(default=_DEFAULT_STYLE_WET_TEMP)
    constant_dry_temp: CurveStyle = Field(default=_DEFAULT_STYLE_DRY_TEMP)
    constant_humidity: CurveStyle = Field(default=_DEFAULT_STYLE_HUMID)
    constant_v_annotation: AnnotationStyle = Field(
        default=_DEFAULT_STYLE_CURVES_ANNOTATION
    )
    constant_h_annotation: AnnotationStyle = Field(
        default=_DEFAULT_STYLE_CURVES_ANNOTATION
    )
    constant_wet_temp_annotation: AnnotationStyle = Field(
        default=_DEFAULT_STYLE_CURVES_ANNOTATION
    )
    constant_rh_annotation: AnnotationStyle = Field(
        default=_DEFAULT_STYLE_CURVES_ANNOTATION
    )

    chart_params: ChartParams = Field(default_factory=ChartParams)

    @property
    def dbt_min(self) -> float:
        """Left limit for chart."""
        return self.limits.range_temp_c[0]

    @property
    def dbt_max(self) -> float:
        """Right limit for chart."""
        return self.limits.range_temp_c[1]

    @property
    def w_min(self) -> float:
        """Bottom limit for chart."""
        return self.limits.range_humidity_g_kg[0]

    @property
    def w_max(self) -> float:
        """Top limit for chart."""
        return self.limits.range_humidity_g_kg[1]


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
