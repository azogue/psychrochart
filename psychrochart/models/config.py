from pydantic import BaseModel, Extra, Field

from psychrochart.models.styles import CurveStyle, LabelStyle, TickStyle

_DEFAULT_RANGE_VOL_M3_KG = (0.78, 0.98)
_DEFAULT_RANGE_ENTALPHY = (5, 155)
_DEFAULT_RANGE_WET_TEMP = (-10, 40)
_DEFAULT_POSITION = [0.025, 0.075, 0.925, 0.875]

_DEFAULT_RH_CURVES = [10, 20, 30, 40, 45, 50, 55, 60, 70, 80, 90]
_DEFAULT_CONSTANT_RH_LABELS = [20, 30, 40, 50, 60, 70, 80]
_DEFAULT_CONSTANT_V_LABELS = [0.8, 0.9, 0.96]
_DEFAULT_CONSTANT_H_LABELS = [5, 25, 50, 75, 100, 125]
_DEFAULT_CONSTANT_WET_TEMP_LABELS = [0, 5, 10, 15, 20, 25, 30, 35]

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


class ChartFigure(BaseModel):
    """Psychrochart settings for matplotlib Figure."""

    figsize: tuple[float, float] = Field(default=(16, 9))
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


class ChartLimits(BaseModel):
    """Psychrochart temperature + humidity + pressure limits."""

    range_temp_c: tuple[float, float] = Field(default=(0, 50))
    range_humidity_g_kg: tuple[float, float] = Field(default=(0, 40))
    altitude_m: int = Field(default=0)
    pressure_kpa: float | None = Field(default=None)
    step_temp: float = Field(default=1)


class ChartParams(BaseModel):
    """Psychrochart plotting parameters."""

    with_constant_rh: bool = Field(default=True)
    constant_rh_label: str | None = Field(default="Constant relative humidity")
    constant_rh_curves: list[int] = Field(default=_DEFAULT_RH_CURVES)
    constant_rh_labels: list[float] = Field(
        default=_DEFAULT_CONSTANT_RH_LABELS
    )
    constant_rh_labels_loc: float = Field(default=0.85)

    with_constant_v: bool = Field(default=True)
    constant_v_label: str | None = Field(default="Constant specific volume")
    constant_v_step: float = Field(default=0.02)
    range_vol_m3_kg: tuple[float, float] = Field(
        default=_DEFAULT_RANGE_VOL_M3_KG
    )
    constant_v_labels: list[float] = Field(default=_DEFAULT_CONSTANT_V_LABELS)
    constant_v_labels_loc: float = Field(default=1.0)

    with_constant_h: bool = Field(default=True)
    constant_h_label: str | None = Field(default="Constant enthalpy")
    constant_h_step: float = Field(default=5)
    range_h: tuple[float, float] = Field(default=_DEFAULT_RANGE_ENTALPHY)
    constant_h_labels: list[float] = Field(default=_DEFAULT_CONSTANT_H_LABELS)
    constant_h_labels_loc: float = Field(default=1.0)

    with_constant_wet_temp: bool = Field(default=True)
    constant_wet_temp_label: str | None = Field(
        default="Constant wet bulb temperature"
    )
    constant_wet_temp_step: float = Field(default=5)
    range_wet_temp: tuple[float, float] = Field(
        default=_DEFAULT_RANGE_WET_TEMP
    )
    constant_wet_temp_labels: list[float] = Field(
        default=_DEFAULT_CONSTANT_WET_TEMP_LABELS
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


class ChartConfig(BaseModel):
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

    chart_params: ChartParams = Field(default_factory=ChartParams)

    class Config:
        extra = Extra.ignore

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
