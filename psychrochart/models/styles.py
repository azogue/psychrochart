from pydantic import BaseModel, Extra, Field, root_validator, validator

from psychrochart.models.validators import parse_color, reduce_field_abrs


class CurveStyle(BaseModel):
    """Container for matplotlib styling of psychro curve."""

    color: list[float] = Field(default=[0.2, 0.2, 0.2])
    linewidth: float = Field(default=1)
    linestyle: str = Field(default="-")

    class Config:
        extra = Extra.allow

    @validator("color", pre=True, always=True)
    def _color_arr(cls, v, values):
        return parse_color(v)

    @root_validator(pre=True)
    def _remove_aliases(cls, values):
        return reduce_field_abrs(values)


class LabelStyle(BaseModel):
    """Container for matplotlib styling of labels."""

    color: list[float] = Field(default=[0.2, 0.2, 0.2])
    fontsize: int | float = Field(default=9)

    class Config:
        extra = Extra.allow

    @validator("color", pre=True, always=True)
    def _color_arr(cls, v, values):
        return parse_color(v)


class TickStyle(BaseModel):
    """Container for matplotlib tick axes styling."""

    direction: str = Field(default="out")
    color: list[float] = Field(default=[0.2, 0.2, 0.2])

    class Config:
        extra = Extra.allow

    @validator("color", pre=True, always=True)
    def _color_arr(cls, v, values):
        return parse_color(v)


class ZoneStyle(BaseModel):
    """Container for matplotlib patch styling of zones in psychrochart."""

    edgecolor: list[float]
    facecolor: list[float]
    linewidth: float = Field(default=2)
    linestyle: str = Field(default="--")

    class Config:
        extra = Extra.allow

    @validator("edgecolor", "facecolor", pre=True, always=True)
    def _color_arr(cls, v, values):
        return parse_color(v)

    @root_validator(pre=True)
    def _remove_aliases(cls, values):
        return reduce_field_abrs(values)
