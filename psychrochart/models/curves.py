import numpy as np
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    model_validator,
)

from psychrochart.models.styles import AnnotationStyle, CurveStyle, ZoneStyle
from psychrochart.models.validators import parse_curve_arrays


class PsychroCurve(BaseModel):
    """Pydantic model to store a psychrometric curve for plotting."""

    x_data: np.ndarray
    y_data: np.ndarray
    style: ZoneStyle | CurveStyle
    type_curve: str | None = None
    label: str | None = None
    label_loc: float = 0.75
    internal_value: float | None = None
    annotation_style: AnnotationStyle | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("x_data", "y_data")
    def _serialize_arrays(self, values: np.ndarray, _info):
        return values.tolist()

    @model_validator(mode="before")
    @classmethod
    def _parse_curve_data(cls, values):
        if (
            values.get("label") is None
            and values.get("internal_value") is None
        ):
            raise ValueError(
                "PsychroCurve should have a 'label' or an 'internal_value'"
            )
        return parse_curve_arrays(values)

    @property
    def curve_id(self) -> str:
        """Get Curve identifier (value or label)."""
        if self.internal_value is not None:
            return f"{self.internal_value:g}".replace("-", "minus")
        assert self.label is not None
        return self.label

    def __repr__(self) -> str:
        """Object string representation."""
        name = (
            "PsychroZone"
            if isinstance(self.style, ZoneStyle)
            else "PsychroCurve"
        )
        extra = f" (label: {self.label})" if self.label else ""
        return f"<{name} {len(self.x_data)} values{extra}>"

    def outside_limits(
        self, xmin: float, xmax: float, ymin: float, ymax: float
    ) -> bool:
        """Test if curve is invisible (outside box)."""
        return (
            max(self.y_data) < ymin
            or max(self.x_data) < xmin
            or min(self.y_data) > ymax
            or min(self.x_data) > xmax
        )


class PsychroCurves(BaseModel):
    """Pydantic model to store a list of psychrometric curves for plotting."""

    curves: list[PsychroCurve] = Field(min_length=1)
    family_label: str | None = None

    def __repr__(self) -> str:
        """Object string representation."""
        extra = f" (label: {self.family_label})" if self.family_label else ""
        return f"<{len(self.curves)} PsychroCurves{extra}>"


class PsychroChartModel(BaseModel):
    """Pydantic model to store all psychrometric curves for PsychroChart."""

    unit_system_si: bool
    altitude_m: int
    pressure: float

    saturation: PsychroCurve
    constant_dry_temp_data: PsychroCurves | None = None
    constant_humidity_data: PsychroCurves | None = None
    constant_rh_data: PsychroCurves | None = None
    constant_h_data: PsychroCurves | None = None
    constant_v_data: PsychroCurves | None = None
    constant_wbt_data: PsychroCurves | None = None
    zones: list[PsychroCurve] = Field(default_factory=list)
