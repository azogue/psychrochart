# -*- coding: utf-8 -*-
"""A library to make psychrometric charts and overlay information in them."""
import json
import logging
from math import atan2, degrees
from typing import AnyStr, Dict, List, Optional

import numpy as np
from matplotlib import patches
from matplotlib.axes import Axes
from matplotlib.path import Path

from .util import mod_color


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


class PsychroCurve:
    """Object to store a psychrometric curve for plotting."""

    def __init__(
        self,
        x_data: np.ndarray = None,
        y_data: np.ndarray = None,
        style: dict = None,
        type_curve: str = None,
        limits: dict = None,
        label: str = None,
        label_loc: float = 0.75,
    ) -> None:
        """Create the Psychrocurve object."""
        self.x_data = np.array(x_data if x_data is not None else [])
        self.y_data = np.array(y_data if y_data is not None else [])
        self.style: dict = style or {}
        self._type_curve = type_curve
        self._label = label
        self._label_loc = label_loc
        self._limits = limits
        self._is_patch: bool = (style is not None and "facecolor" in style)

    def __bool__(self) -> bool:
        """Return the valid existence of the curve."""
        if (
            self.x_data is not None
            and len(self.x_data) > 1
            and self.y_data is not None
            and len(self.y_data) > 1
        ):
            return True
        return False

    def __repr__(self) -> str:
        """Object string representation."""
        name = "PsychroZone" if self._is_patch else "PsychroCurve"
        if self and self.x_data is not None:
            return f"<{name} {len(self.x_data)} values (label: {self._label})>"
        else:
            return f"<Empty {name} (label: {self._label})>"

    def to_dict(self) -> Dict:
        """Return the curve as a dict."""
        if len(self.x_data) == 0 or len(self.y_data) == 0:
            return {}
        return {
            "x_data": self.x_data.tolist(),
            "y_data": self.y_data.tolist(),
            "style": self.style,
            "label": self._label,
        }

    def to_json(self) -> str:
        """Return the curve as a JSON string."""
        return json.dumps(self.to_dict())

    def from_json(self, json_str: AnyStr):
        """Load a curve from a JSON string."""
        data = json.loads(json_str)
        self.x_data = np.array(data["x_data"])
        self.y_data = np.array(data["y_data"])
        self.style = data.get("style")
        self._label = data.get("label")
        return self

    @staticmethod
    def _annotate_label(
        ax: Axes,
        label: AnyStr,
        text_x: float,
        text_y: float,
        rotation: float,
        text_style: Dict,
    ):
        if abs(rotation) > 0:
            text_loc = np.array((text_x, text_y))
            text_style["rotation"] = ax.transData.transform_angles(
                np.array((rotation,)), text_loc.reshape((1, 2))
            )[0]
            text_style["rotation_mode"] = "anchor"
        ax.annotate(label, (text_x, text_y), **text_style)

    def plot(self, ax: Axes) -> Axes:
        """Plot the curve."""
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
                f"{self._type_curve} (label:{self._label}) Not between limits "
                f"([{xmin}, {xmax}, {ymin}, {ymax}]) "
                f"-> x:{self.x_data}, y:{self.y_data}"
            )
            return ax

        if self._is_patch and self.y_data is not None:
            assert len(self.y_data) > 2
            verts = list(zip(self.x_data, self.y_data))
            codes = (
                [Path.MOVETO]
                + [Path.LINETO] * (len(self.y_data) - 2)
                + [Path.CLOSEPOLY]
            )
            path = Path(verts, codes)
            patch = patches.PathPatch(path, **self.style)
            ax.add_patch(patch)

            if self._label is not None:
                bbox_p = path.get_extents()
                text_x = 0.5 * (bbox_p.x0 + bbox_p.x1)
                text_y = 0.5 * (bbox_p.y0 + bbox_p.y1)
                style = {
                    "ha": "center",
                    "va": "center",
                    "backgroundcolor": [1, 1, 1, 0.4],
                }
                if "edgecolor" in self.style:
                    style["color"] = mod_color(self.style["edgecolor"], -25)
                self._annotate_label(ax, self._label, text_x, text_y, 0, style)
        else:
            ax.plot(self.x_data, self.y_data, **self.style)
            if self._label is not None:
                self.add_label(ax)

        return ax

    def add_label(
        self,
        ax: Axes,
        text_label: str = None,
        va: str = None,
        ha: str = None,
        loc: float = None,
        **params,
    ) -> Axes:
        """Annotate the curve with its label."""
        num_samples = len(self.x_data)
        assert num_samples > 1
        text_style = {"va": "bottom", "ha": "left", "color": [0.0, 0.0, 0.0]}
        loc_f: float = self._label_loc if loc is None else loc
        label: str = (
            (self._label if self._label is not None else "")
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

        if "color" in self.style:
            text_style["color"] = mod_color(self.style["color"], -25)
        if ha is not None:
            text_style["ha"] = ha
        if va is not None:
            text_style["va"] = va
        if params:
            text_style.update(params)

        self._annotate_label(ax, label, text_x, text_y, rotation, text_style)

        return ax


class PsychroCurves:
    """Object to store a list of psychrometric curves for plotting."""

    def __init__(
        self, curves: List[PsychroCurve], family_label: str = None
    ) -> None:
        """Create the Psychrocurves array object."""
        self.curves: List[PsychroCurve] = curves
        self.size: int = len(self.curves)
        self.family_label: Optional[str] = family_label

    def __getitem__(self, item) -> PsychroCurve:
        """Get item from the PsychroCurve list."""
        return self.curves[item]

    def __repr__(self) -> str:
        """Object string representation."""
        return f"<{self.size} PsychroCurves (label: {self.family_label})>"

    def plot(self, ax: Axes) -> Axes:
        """Plot the family curves."""
        [curve.plot(ax) for curve in self.curves]

        # Curves family labelling
        if self.curves and self.family_label is not None:
            style = self.curves[0].style or {}
            ax.plot(
                [-1],
                [-1],
                label=self.family_label,
                marker="D",
                markersize=10,
                **style,
            )

        return ax
