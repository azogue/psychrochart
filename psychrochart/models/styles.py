from typing import Any

from pydantic import ConfigDict, Field, field_validator, model_validator

from psychrochart.models.base import BaseConfig
from psychrochart.models.validators import parse_color, reduce_field_abrs


class CurveStyle(BaseConfig):
    """Container for matplotlib styling of psychro curve."""

    color: list[float] = Field(default=[0.2, 0.2, 0.2])
    linewidth: float = Field(default=1)
    linestyle: str = Field(default="-")

    model_config = ConfigDict(extra="allow")

    @field_validator("color", mode="before")
    @classmethod
    def _color_arr(cls, value):
        return parse_color(value)

    @model_validator(mode="before")
    @classmethod
    def _remove_aliases(cls, values):
        return reduce_field_abrs(values)


class LabelStyle(BaseConfig):
    """Container for matplotlib styling of labels."""

    color: list[float] = Field(default=[0.2, 0.2, 0.2])
    fontsize: int | float = Field(default=9)

    model_config = ConfigDict(extra="allow")

    @field_validator("color", mode="before")
    @classmethod
    def _color_arr(cls, value):
        return parse_color(value)


class AnnotationStyle(BaseConfig):
    """Container for matplotlib styling of curve annotations."""

    color: list[float] | None = None
    fontsize: int | float = Field(default=9)
    bbox: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")

    @field_validator("color", mode="before")
    @classmethod
    def _color_arr(cls, value):
        return parse_color(value) if value else None

    def export_style(self) -> dict[str, Any]:
        """Get enabled styling kwargs for curve annotation."""
        return {
            key: value for key, value in self.model_dump().items() if value
        }


class TickStyle(BaseConfig):
    """Container for matplotlib tick axes styling."""

    direction: str = Field(default="out")
    color: list[float] = Field(default=[0.2, 0.2, 0.2])

    model_config = ConfigDict(extra="allow")

    @field_validator("color", mode="before")
    @classmethod
    def _color_arr(cls, value):
        return parse_color(value)


class ZoneStyle(BaseConfig):
    """Container for matplotlib patch styling of zones in psychrochart."""

    edgecolor: list[float]
    facecolor: list[float]
    linewidth: float = Field(default=2)
    linestyle: str = Field(default="--")

    model_config = ConfigDict(extra="allow")

    @field_validator("edgecolor", "facecolor", mode="before")
    @classmethod
    def _color_arr(cls, value):
        return parse_color(value)

    @model_validator(mode="before")
    @classmethod
    def _remove_aliases_and_fix_defaults(cls, values):
        if isinstance(values, dict):
            if values.get("linewidth", 2) == 0:
                # avoid matplotlib error with inconsistent line parameters
                values["linestyle"] = "-"
            return reduce_field_abrs(values)
        return values
