import logging
from math import atan2, degrees
from typing import AbstractSet, Any, AnyStr, Mapping

from matplotlib import patches
from matplotlib.axes import Axes
from matplotlib.path import Path
import numpy as np
from pydantic import BaseModel, Field, root_validator

from psychrochart.models.styles import CurveStyle, ZoneStyle
from psychrochart.models.validators import parse_curve_arrays
from psychrochart.util import mod_color


def _between_limits(
    x_data: np.ndarray,
    y_data: np.ndarray,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
) -> bool:
    data_xmin = min(x_data)
    data_xmax = max(x_data)
    data_ymin = min(y_data)
    data_ymax = max(y_data)
    if (
        (data_ymax < ymin)
        or (data_xmax < xmin)
        or (data_ymin > ymax)
        or (data_xmin > xmax)
    ):
        return False
    return True


def _annotate_label(
    ax: Axes,
    label: AnyStr,
    text_x: float,
    text_y: float,
    rotation: float,
    text_style: dict[str, Any],
) -> None:
    if abs(rotation) > 0:
        text_loc = np.array((text_x, text_y))
        text_style["rotation"] = ax.transData.transform_angles(
            np.array((rotation,)), text_loc.reshape((1, 2))
        )[0]
        text_style["rotation_mode"] = "anchor"
    ax.annotate(label, (text_x, text_y), **text_style)


class PsychroCurve(BaseModel):
    """Pydantic model to store a psychrometric curve for plotting."""

    x_data: np.ndarray
    y_data: np.ndarray
    style: ZoneStyle | CurveStyle
    type_curve: str | None = None
    label: str | None = None
    label_loc: float = 0.75

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {np.ndarray: lambda x: x.tolist()}

    @root_validator(pre=True)
    def _parse_curve_data(cls, values):
        return parse_curve_arrays(values)

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

    def plot_curve(self, ax: Axes) -> bool:
        """Plot the curve, if it's between chart limits."""
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        if (
            self.x_data is None
            or self.y_data is None
            or not _between_limits(
                self.x_data, self.y_data, xmin, xmax, ymin, ymax
            )
        ):
            logging.info(
                "%s (label:%s) not between limits ([%.2g, %.2g, %.2g, %.2g]) "
                "-> x:%s, y:%s",
                self.type_curve,
                self.label or "unnamed",
                xmin,
                xmax,
                ymin,
                ymax,
                self.x_data,
                self.y_data,
            )
            return False

        if isinstance(self.style, ZoneStyle):
            assert len(self.y_data) > 2
            verts = list(zip(self.x_data, self.y_data))
            codes = (
                [Path.MOVETO]
                + [Path.LINETO] * (len(self.y_data) - 2)
                + [Path.CLOSEPOLY]
            )
            path = Path(verts, codes)
            patch = patches.PathPatch(path, **self.style.dict())
            ax.add_patch(patch)

            if self.label is not None:
                bbox_p = path.get_extents()
                text_x = 0.5 * (bbox_p.x0 + bbox_p.x1)
                text_y = 0.5 * (bbox_p.y0 + bbox_p.y1)
                style_params = {
                    "ha": "center",
                    "va": "center",
                    "backgroundcolor": [1, 1, 1, 0.4],
                }
                assert isinstance(self.style, ZoneStyle)
                style_params["color"] = mod_color(self.style.edgecolor, -25)
                _annotate_label(
                    ax, self.label, text_x, text_y, 0, style_params
                )
        else:
            ax.plot(self.x_data, self.y_data, **self.style.dict())
            if self.label is not None:
                self.add_label(ax)
        return True

    def add_label(
        self,
        ax: Axes,
        text_label: str | None = None,
        va: str | None = None,
        ha: str | None = None,
        loc: float | None = None,
        **params,
    ) -> Axes:
        """Annotate the curve with its label."""
        num_samples = len(self.x_data)
        assert num_samples > 1
        text_style = {"va": "bottom", "ha": "left", "color": [0.0, 0.0, 0.0]}
        loc_f: float = self.label_loc if loc is None else loc
        label: str = (
            (self.label if self.label is not None else "")
            if text_label is None
            else text_label
        )

        def _tilt_params(x_data, y_data, idx_0, idx_f):
            delta_x = x_data[idx_f] - self.x_data[idx_0]
            delta_y = y_data[idx_f] - self.y_data[idx_0]
            rotation_deg = degrees(atan2(delta_y, delta_x))
            if delta_x == 0:
                tilt_curve = 1e12
            else:
                tilt_curve = delta_y / delta_x
            return rotation_deg, tilt_curve

        if num_samples == 2:
            xmin, xmax = ax.get_xlim()
            rotation, tilt = _tilt_params(self.x_data, self.y_data, 0, 1)
            if abs(rotation) == 90:
                text_x = self.x_data[0]
                text_y = self.y_data[0] + loc_f * (
                    self.y_data[1] - self.y_data[0]
                )
            elif loc_f == 1.0:
                if self.x_data[1] > xmax:
                    text_x = xmax
                    text_y = self.y_data[0] + tilt * (xmax - self.x_data[0])
                else:
                    text_x, text_y = self.x_data[1], self.y_data[1]
                label += "    "
                text_style["ha"] = "right"
            else:
                text_x = self.x_data[0] + loc_f * (xmax - xmin)
                if text_x < xmin:
                    text_x = xmin + loc_f * (xmax - xmin)
                text_y = self.y_data[0] + tilt * (text_x - self.x_data[0])
        else:
            idx = min(num_samples - 2, int(num_samples * loc_f))
            rotation, tilt = _tilt_params(
                self.x_data, self.y_data, idx, idx + 1
            )
            text_x, text_y = self.x_data[idx], self.y_data[idx]
            text_style["ha"] = "center"

        text_style["color"] = mod_color(self.style.color, -25)
        if ha is not None:
            text_style["ha"] = ha
        if va is not None:
            text_style["va"] = va
        if params:
            text_style.update(params)

        _annotate_label(ax, label, text_x, text_y, rotation, text_style)

        return ax


class PsychroCurves(BaseModel):
    """Pydantic model to store a list of psychrometric curves for plotting."""

    curves: list[PsychroCurve] = Field(min_items=1)
    family_label: str | None = None

    def __repr__(self) -> str:
        """Object string representation."""
        extra = f" (label: {self.family_label})" if self.family_label else ""
        return f"<{len(self.curves)} PsychroCurves{extra}>"

    def plot(self, ax: Axes) -> Axes:
        """Plot the family curves."""
        [curve.plot_curve(ax) for curve in self.curves]

        # Curves family labelling
        if self.curves and self.family_label is not None:
            ax.plot(
                [-1],
                [-1],
                label=self.family_label,
                marker="D",
                markersize=10,
                **self.curves[0].style.dict(),
            )

        return ax


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
