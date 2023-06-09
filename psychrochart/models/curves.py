from typing import AbstractSet, Any, Mapping

import numpy as np
from pydantic import BaseModel, Field, root_validator

from psychrochart.models.styles import CurveStyle, ZoneStyle
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

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {np.ndarray: lambda x: x.tolist()}

    @root_validator(pre=True)
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
            return f"{self.internal_value:g}"
        assert self.label is not None
        return self.label

    def dict(
        self,
        *,
        include: AbstractSet[int | str]
        | Mapping[int | str, Any]
        | None = None,
        exclude: AbstractSet[int | str]
        | Mapping[int | str, Any]
        | None = None,
        by_alias: bool = False,
        skip_defaults: bool | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> dict[str, Any]:
        """Override pydantic.BaseModel.dict() to export arrays as list."""
        plain_dict = super().dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        plain_dict["x_data"] = plain_dict["x_data"].tolist()
        plain_dict["y_data"] = plain_dict["y_data"].tolist()
        return plain_dict

    def __repr__(self) -> str:
        """Object string representation."""
        name = (
            "PsychroZone"
            if isinstance(self.style, ZoneStyle)
            else "PsychroCurve"
        )
        extra = f" (label: {self.label})" if self.label else ""
        return f"<{name} {len(self.x_data)} values{extra}>"


class PsychroCurves(BaseModel):
    """Pydantic model to store a list of psychrometric curves for plotting."""

    curves: list[PsychroCurve] = Field(min_items=1)
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

    saturation: PsychroCurves
    constant_dry_temp_data: PsychroCurves | None = None
    constant_humidity_data: PsychroCurves | None = None
    constant_rh_data: PsychroCurves | None = None
    constant_h_data: PsychroCurves | None = None
    constant_v_data: PsychroCurves | None = None
    constant_wbt_data: PsychroCurves | None = None
    zones: list[PsychroCurves] = Field(default_factory=list)
