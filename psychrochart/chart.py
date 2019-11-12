# -*- coding: utf-8 -*-
"""A library to make psychrometric charts and overlay information in them."""
import gc
import logging
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import numpy as np
import psychrolib as psy
from matplotlib import figure
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.legend import Legend
from psychrolib import GetStandardAtmPressure, IP, SetUnitSystem, SI
from scipy.spatial import ConvexHull
from scipy.spatial.qhull import QhullError

from .chartdata import (
    gen_points_in_constant_relative_humidity,
    make_constant_dry_bulb_v_line,
    make_constant_dry_bulb_v_lines,
    make_constant_enthalpy_lines,
    make_constant_humidity_ratio_h_lines,
    make_constant_relative_humidity_lines,
    make_constant_specific_volume_lines,
    make_constant_wet_bulb_temperature_lines,
    make_saturation_line,
    make_zone_curve,
)
from .psychrocurves import PsychroCurves
from .util import load_config, load_zones, mod_color

spec_vol_vec = np.vectorize(psy.GetMoistAirVolume)

PSYCHRO_CURVES_KEYS = [
    "constant_dry_temp_data",
    "constant_humidity_data",
    "constant_h_data",
    "constant_v_data",
    "constant_rh_data",
    "constant_wbt_data",
    "saturation",
]


class PsychroChart:
    """Psychrometric chart object handler."""

    def __init__(
        self,
        styles: Union[dict, str] = None,
        zones_file: Union[dict, str] = None,
        use_unit_system_si: bool = True,
    ) -> None:
        """Create the PsychroChart object."""
        self.d_config: dict = {}
        self.figure_params: dict = {}
        self.dbt_min = self.dbt_max = -100
        self.w_min = self.w_max = -1
        self.temp_step = 1.0
        self.altitude_m = -1
        self.chart_params: dict = {}

        # Set unit system for psychrolib and get standard pressure
        self.unit_system_si = use_unit_system_si
        if use_unit_system_si:
            SetUnitSystem(SI)
            logging.info("[SI units mode] ENABLED")
        else:
            SetUnitSystem(IP)
            logging.warning("[IP units mode] ENABLED")
        self.pressure = GetStandardAtmPressure(0.0)

        self.constant_dry_temp_data: Optional[PsychroCurves] = None
        self.constant_humidity_data: Optional[PsychroCurves] = None
        self.constant_rh_data: Optional[PsychroCurves] = None
        self.constant_h_data: Optional[PsychroCurves] = None
        self.constant_v_data: Optional[PsychroCurves] = None
        self.constant_wbt_data: Optional[PsychroCurves] = None
        self.saturation: Optional[PsychroCurves] = None
        self.zones: List = []

        self._fig: Optional[figure.Figure] = None
        self._canvas: Optional[FigureCanvas] = None
        self._axes: Optional[Axes] = None
        self._legend: Optional[Legend] = None
        self._handlers_annotations: List = []

        self._make_chart_data(styles, zones_file)

    def __repr__(self) -> str:
        """Return a string representation of the PsychroChart object."""
        return (
            f"<PsychroChart [{self.dbt_min:g}->{self.dbt_max:g} °C, "
            f"{self.w_min:g}->{self.w_max:g} gr/kg_da]>"
        )

    @property
    def axes(self) -> Axes:
        """Return the Axes object plotting the chart if necessary."""
        if self._axes is None:
            self.plot()
        assert isinstance(self._axes, Axes)
        return self._axes

    @property
    def figure(self) -> figure.Figure:
        """Return the Figure object, plotting the chart if necessary."""
        if self._fig is None:
            self.plot()
        assert isinstance(self._fig, figure.Figure)
        return self._fig

    def _make_chart_data(
        self,
        styles: Union[dict, str] = None,
        zones_file: Union[dict, str] = None,
    ) -> None:
        """Generate the data to plot the psychrometric chart."""
        # Get styling
        config = load_config(styles)
        self.d_config = config
        self.temp_step = config["limits"]["step_temp"]

        self.figure_params = config["figure"]
        self.dbt_min, self.dbt_max = config["limits"]["range_temp_c"]
        self.w_min, self.w_max = config["limits"]["range_humidity_g_kg"]

        self.chart_params = config["chart_params"].copy()

        # Base pressure
        if config["limits"].get("pressure_kpa") is not None:
            self.pressure = config["limits"]["pressure_kpa"] * 1000.0  # to Pa
        elif config["limits"].get("altitude_m") is not None:
            self.altitude_m = config["limits"]["altitude_m"]
            self.pressure = GetStandardAtmPressure(self.altitude_m)

        # Saturation line (always):
        self.saturation = make_saturation_line(
            self.dbt_min,
            self.dbt_max,
            self.temp_step,
            self.pressure,
            style=config["saturation"],
        )

        # Dry bulb constant lines (vertical):
        if self.chart_params["with_constant_dry_temp"]:
            step = self.chart_params["constant_temp_step"]
            self.constant_dry_temp_data = make_constant_dry_bulb_v_lines(
                self.w_min,
                self.pressure,
                temps_vl=np.arange(self.dbt_min, self.dbt_max, step),
                style=config["constant_dry_temp"],
                family_label=self.chart_params["constant_temp_label"],
            )

        # Absolute humidity constant lines (horizontal):
        if self.chart_params["with_constant_humidity"]:
            step = self.chart_params["constant_humid_step"]
            self.constant_humidity_data = make_constant_humidity_ratio_h_lines(
                self.dbt_max,
                self.pressure,
                ws_hl=np.arange(
                    self.w_min + step, self.w_max + step / 10, step
                ),
                style=config["constant_humidity"],
                family_label=self.chart_params["constant_humid_label"],
            )

        # Constant relative humidity curves:
        if self.chart_params["with_constant_rh"]:
            self.constant_rh_data = make_constant_relative_humidity_lines(
                self.dbt_min,
                self.dbt_max,
                self.temp_step,
                self.pressure,
                rh_perc_values=self.chart_params["constant_rh_curves"],
                rh_label_values=self.chart_params.get(
                    "constant_rh_labels", []
                ),
                style=config["constant_rh"],
                label_loc=self.chart_params.get(
                    "constant_rh_labels_loc", 0.85
                ),
                family_label=self.chart_params["constant_rh_label"],
            )

        # Constant enthalpy lines:
        if self.chart_params["with_constant_h"]:
            step = self.chart_params["constant_h_step"]
            start, end = self.chart_params["range_h"]
            self.constant_h_data = make_constant_enthalpy_lines(
                self.w_min,
                self.pressure,
                enthalpy_values=np.arange(start, end, step),
                h_label_values=self.chart_params.get("constant_h_labels", []),
                style=config["constant_h"],
                label_loc=self.chart_params.get("constant_h_labels_loc", 1.0),
                family_label=self.chart_params["constant_h_label"],
                saturation_curve=self.saturation.curves[0],
            )

        # Constant specific volume lines:
        if self.chart_params["with_constant_v"]:
            step = self.chart_params["constant_v_step"]
            start, end = self.chart_params["range_vol_m3_kg"]
            self.constant_v_data = make_constant_specific_volume_lines(
                self.w_min,
                self.pressure,
                vol_values=np.arange(start, end, step),
                v_label_values=self.chart_params.get("constant_v_labels", []),
                style=config["constant_v"],
                label_loc=self.chart_params.get("constant_v_labels_loc", 1.0),
                family_label=self.chart_params["constant_v_label"],
                saturation_curve=self.saturation.curves[0],
            )

        # Constant wet bulb temperature lines:
        if self.chart_params["with_constant_wet_temp"]:
            step = self.chart_params["constant_wet_temp_step"]
            start, end = self.chart_params["range_wet_temp"]
            self.constant_wbt_data = make_constant_wet_bulb_temperature_lines(
                self.dbt_max,
                self.pressure,
                wbt_values=np.arange(start, end, step),
                wbt_label_values=self.chart_params.get(
                    "constant_wet_temp_labels", []
                ),
                style=config["constant_wet_temp"],
                label_loc=self.chart_params.get(
                    "constant_wet_temp_labels_loc", 0.05
                ),
                family_label=self.chart_params["constant_wet_temp_label"],
            )

        # Zones
        if self.chart_params["with_zones"] or zones_file is not None:
            self.append_zones(zones_file)

    def append_zones(self, zones: Union[dict, str] = None) -> None:
        """Append zones as patches to the psychrometric chart."""
        if zones is None:
            # load default 'Comfort' zones (Spain RITE)
            d_zones = load_zones()
        else:
            d_zones = load_zones(zones)

        zones_ok = [
            make_zone_curve(zone_conf, self.temp_step, self.pressure)
            for zone_conf in d_zones["zones"]
            if zone_conf["zone_type"] in ("dbt-rh", "xy-points")
        ]
        if zones_ok:
            self.zones.append(PsychroCurves(zones_ok))

    def plot_points_dbt_rh(
        self,
        points: Dict,
        connectors: list = None,
        convex_groups: list = None,
        scatter_style: dict = None,
    ) -> Dict:
        """Append individual points, connectors and groups to the plot.

        * Pass a specific style dict to do a scatter plot:
            `scatter_style={'s': 5, 'alpha': .1, 'color': 'darkorange'}`

        * if you are plotting series of points, pass them as numpy arrays:
            `points={'points_series_name': (temp_array, humid_array)}`

        - The syntax to add points is:
        ```
        points = {
            'point_1_name': {
                'label': 'label_for_legend',
                'style': {'color': [0.855, 0.004, 0.278, 0.8],
                          'marker': 'X', 'markersize': 15},
                'xy': (31.06, 32.9)},
            'point_2_name': {
                'label': 'label_for_legend',
                'style': {'color': [0.573, 0.106, 0.318, 0.5],
                          'marker': 'x',
                          'markersize': 10},
                'xy': (29.42, 52.34)},
                # ...
        }
        # Or, using the default style:
        points = {
            'point_1_name': (31.06, 32.9),
            'point_2_name': (29.42, 52.34),
            # ...
        }
        ```

        - The syntax to add connectors between pairs of given points is:
        ```
        connectors = [
            {'start': 'point_1_name',
             'end': 'point_2_name',
             'style': {'color': [0.573, 0.106, 0.318, 0.7],
                       "linewidth": 2, "linestyle": "-."}},
            {'start': 'point_2_name',
             'end': 'point_3_name',
             'style': {'color': [0.855, 0.145, 0.114, 0.8],
                       "linewidth": 2, "linestyle": ":"}},
            # ...
        ]
        ```

        - The syntax to add groups of given points (with more than 3 points)
         to plot a styled convex hull area is:
        ```
        interior_zones = [
            # Zone 1:
            ([point_1_name, point_2_name, point_3_name, ...],  # list of points
             {"color": 'darkgreen', "lw": 0, ...},             # line style
             {"color": 'darkgreen', "lw": 0, ...}),            # filling style

            # Zone 2:
            ([point_7_name, point_8_name, point_9_name, ...],  # list of points
             {"color": 'darkorange', "lw": 0, ...},            # line style
             {"color": 'darkorange', "lw": 0, ...}),           # filling style

            # ...
        ]
        ```
        """
        use_scatter = False
        points_plot: Dict[str, Tuple[List[float], List[float], dict]] = {}
        default_style = {
            "marker": "o",
            "markersize": 10,
            "color": [1.0, 0.8, 0.1, 0.8],
            "linewidth": 0,
        }
        if scatter_style is not None:
            default_style = scatter_style
            use_scatter = True

        for key, point in points.items():
            plot_params = default_style.copy()
            if isinstance(point, dict):
                plot_params.update(point.get("style", {}))
                plot_params["label"] = point.get("label")
                point = point["xy"]
            temp = point[0]
            temperatures = temp if isinstance(temp, Iterable) else [temp]
            w_g_ka = gen_points_in_constant_relative_humidity(
                temperatures, point[1], self.pressure
            )
            points_plot[key] = [temp], w_g_ka, plot_params

        if connectors is not None:
            for d_con in connectors:
                if (
                    d_con["start"] in points_plot
                    and d_con["end"] in points_plot
                ):
                    x_start = points_plot[d_con["start"]][0][0]
                    y_start = points_plot[d_con["start"]][1][0]
                    x_end = points_plot[d_con["end"]][0][0]
                    y_end = points_plot[d_con["end"]][1][0]
                    x_line = [x_start, x_end]
                    y_line = [y_start, y_end]
                    style = d_con.get("style", points_plot[d_con["start"]][2])
                    line_label = d_con.get("label")
                    self._handlers_annotations.append(
                        self.axes.plot(
                            x_line,
                            y_line,
                            label=line_label,
                            dash_capstyle="round",
                            **style,
                        )
                    )
                    self._handlers_annotations.append(
                        self.axes.plot(
                            x_line,
                            y_line,
                            color=list(style["color"][:3]) + [0.15],
                            lw=50,
                            solid_capstyle="round",
                        )
                    )

        for point in points_plot.values():
            func_append = self.axes.scatter if use_scatter else self.axes.plot
            self._handlers_annotations.append(
                func_append(point[0], point[1], **point[2])
            )

        if (
            ConvexHull is not None
            and convex_groups
            and points_plot
            and (
                isinstance(convex_groups[0], list)
                or isinstance(convex_groups[0], tuple)
            )
            and len(convex_groups[0]) == 3
        ):
            for convex_hull_zone, style_line, style_fill in convex_groups:
                int_points = np.array(
                    [
                        (point[0][0], point[1][0])
                        for name, point in points_plot.items()
                        if name in convex_hull_zone
                    ]
                )

                if len(int_points) < 3:
                    continue

                try:
                    hull = ConvexHull(int_points)
                except QhullError:  # pragma: no cover
                    logging.error(f"QhullError with points: {int_points}")
                    continue

                # noinspection PyUnresolvedReferences
                for simplex in hull.simplices:
                    self._handlers_annotations.append(
                        self.axes.plot(
                            int_points[simplex, 0],
                            int_points[simplex, 1],
                            **style_line,
                        )
                    )
                self._handlers_annotations.append(
                    self.axes.fill(
                        int_points[hull.vertices, 0],
                        int_points[hull.vertices, 1],
                        **style_fill,
                    )
                )

        return points_plot

    def plot_arrows_dbt_rh(self, points_pairs: Dict) -> Dict:
        """Append individual points to the plot."""
        points_plot = {}
        default_style = {
            "linewidth": 0,
            "color": [1.0, 0.8, 0.1, 0.8],
            "arrowstyle": "wedge",
        }
        for key, pair_point in points_pairs.items():
            plot_params = default_style.copy()
            if isinstance(pair_point, dict):
                if "style" in pair_point and "color" in pair_point["style"]:
                    plot_params["color"] = mod_color(
                        pair_point["style"]["color"], 0.6
                    )  # set alpha
                point1, point2 = pair_point["xy"]
            else:
                point1, point2 = pair_point
            temp1 = point1[0]
            temp2 = point2[0]
            w_g_ka1 = gen_points_in_constant_relative_humidity(
                [temp1], point1[1], self.pressure
            )[0]
            w_g_ka2 = gen_points_in_constant_relative_humidity(
                [temp2], point2[1], self.pressure
            )[0]

            self._handlers_annotations.append(
                self.axes.annotate(
                    "",
                    (temp2, w_g_ka2),
                    xytext=(temp1, w_g_ka1),
                    arrowprops=plot_params,
                )
            )

            points_plot[key] = (temp1, w_g_ka1), (temp2, w_g_ka2), plot_params

        return points_plot

    def plot_vertical_dry_bulb_temp_line(
        self,
        temp: float,
        style: dict = None,
        label: str = None,
        reverse: bool = False,
        **label_params,
    ) -> None:
        """Append a vertical line from w_min to w_sat."""
        style_curve = style or self.d_config["constant_dry_temp"]
        curve = make_constant_dry_bulb_v_line(
            self.w_min,
            temp,
            self.pressure,
            style=style_curve,
            reverse=reverse,
        )
        curve.plot(self.axes)
        if label is not None:
            curve.add_label(self.axes, label, **label_params)

    def plot_legend(
        self,
        loc: str = "upper left",
        markerscale: float = 0.9,
        frameon: bool = True,
        fancybox: bool = True,
        edgecolor: Union[str, Iterable] = "darkgrey",
        fontsize: float = 15.0,
        labelspacing: float = 1.5,
        **params,
    ) -> None:
        """Append a legend to the psychrochart plot."""
        self._legend = self.axes.legend(
            loc=loc,
            markerscale=markerscale,
            frameon=frameon,
            edgecolor=edgecolor,
            fontsize=fontsize,
            fancybox=fancybox,
            labelspacing=labelspacing,
            **params,
        )

    def _prepare_fig_and_axis(self, ax: Axes = None) -> Tuple[Axes, dict]:
        """Prepare matplotlib fig & Axes object for the chart."""
        fig_params = self.figure_params.copy()
        figsize = fig_params.pop("figsize", (16, 9))
        position = fig_params.pop("position", [0.025, 0.075, 0.925, 0.875])

        # Create figure and format axis
        self._fig = figure.Figure(figsize=figsize, dpi=150, frameon=False)
        self._canvas = FigureCanvas(self.figure)
        if ax is None:
            ax = self.figure.gca(position=position)
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")
        ax.set_xlim(self.dbt_min, self.dbt_max)
        ax.set_ylim(self.w_min, self.w_max)
        ax.grid(False)
        ax.grid(False, which="minor")

        return ax, fig_params

    def _set_tick_labels_in_main_axes(
        self, ax: Axes, x_style_labels: dict, y_style_labels: dict
    ):
        """Plot the psychrochart and return the matplotlib Axes instance."""
        if self.chart_params.get("with_constant_dry_temp", True):
            step_label = self.chart_params.get(
                "constant_temp_label_step", None
            )
            if step_label:  # Explicit xticks
                ticks = np.arange(
                    self.dbt_min, self.dbt_max + step_label / 10, step_label
                )
                if not self.chart_params.get(
                    "constant_temp_label_include_limits", True
                ):
                    ticks = [
                        t
                        for t in ticks
                        if t not in [self.dbt_min, self.dbt_max]
                    ]
                ax.set_xticks(ticks)
                ax.set_xticklabels([f"{t:g}" for t in ticks], **x_style_labels)
        else:
            ax.set_xticks([])

        if self.chart_params.get("with_constant_humidity", True):
            step_label = self.chart_params.get(
                "constant_humid_label_step", None
            )
            if step_label:  # Explicit xticks
                ticks = np.arange(
                    self.w_min, self.w_max + step_label / 10, step_label
                )
                if not self.chart_params.get(
                    "constant_humid_label_include_limits", True
                ):
                    ticks = [
                        t for t in ticks if t not in [self.w_min, self.w_max]
                    ]
                ax.set_yticks(ticks)
                ax.set_yticklabels([f"{t:g}" for t in ticks], **y_style_labels)
        else:
            ax.set_yticks([])

    def _apply_axis_styling(self, ax: Axes, fig_params: dict):
        """Plot the psychrochart and return the matplotlib Axes instance."""

        def _apply_spines_style(axes, style, location="right"):
            for key in style:
                if (key == "color") or (key == "c"):
                    axes.spines[location].set_color(style[key])
                elif (key == "linewidth") or (key == "lw"):
                    axes.spines[location].set_linewidth(style[key])
                elif (key == "linestyle") or (key == "ls"):
                    axes.spines[location].set_linestyle(style[key])
                else:  # pragma: no cover
                    try:
                        getattr(axes.spines[location], f"set_{key}")(
                            style[key]
                        )
                    except Exception as exc:
                        logging.error(
                            f"Error trying to apply spines attrs: {exc}. "
                            f"({dir(axes.spines[location])})"
                        )

        # Get parameters to style axes
        fontsize = fig_params.pop("fontsize", 10)
        x_style = fig_params.pop("x_axis", {})
        x_style_labels = fig_params.pop("x_axis_labels", {})
        x_style_ticks = fig_params.pop("x_axis_ticks", {})
        y_style = fig_params.pop("y_axis", {})
        y_style_labels = fig_params.pop("y_axis_labels", {})
        y_style_ticks = fig_params.pop("y_axis_ticks", {})
        partial_axis = fig_params.pop("partial_axis", True)

        # Apply axis styles
        if fig_params["x_label"] is not None:
            style_axis = x_style_labels.copy()
            style_axis["fontsize"] *= 1.2
            ax.set_xlabel(fig_params["x_label"], **style_axis)
        if fig_params["y_label"] is not None:
            style_axis = y_style_labels.copy()
            style_axis["fontsize"] *= 1.2
            ax.set_ylabel(fig_params["y_label"], **style_axis)
        if fig_params["title"] is not None:
            ax.set_title(
                fig_params["title"], fontsize=fontsize * 1.5, fontweight="bold"
            )

        _apply_spines_style(ax, y_style, location="right")
        _apply_spines_style(ax, x_style, location="bottom")
        if partial_axis:  # Hide left and top axis
            ax.spines["left"].set_visible(False)
            ax.spines["top"].set_visible(False)
        else:
            _apply_spines_style(ax, y_style, location="left")
            _apply_spines_style(ax, x_style, location="top")

        if x_style_ticks:
            ax.tick_params(axis="x", **x_style_ticks)
        if y_style_ticks:
            ax.tick_params(axis="y", **y_style_ticks)

        self._set_tick_labels_in_main_axes(ax, x_style_labels, y_style_labels)

    def plot(self, ax: Axes = None) -> Axes:
        """Plot the psychrochart and return the matplotlib Axes instance."""
        # Prepare fig & axis
        ax, fig_params = self._prepare_fig_and_axis(ax)

        # Apply axis styles
        self._apply_axis_styling(ax, fig_params)

        # Plot curves:
        [
            getattr(self, curve_family).plot(ax)
            for curve_family in PSYCHRO_CURVES_KEYS
            if getattr(self, curve_family) is not None
        ]

        # Plot zones:
        [zone.plot(ax=ax) for zone in self.zones]

        # Set the Axes object
        self._axes = ax
        return ax

    def remove_annotations(self) -> None:
        """Remove the annotations made in the chart to reuse it."""
        for line in self._handlers_annotations:
            try:
                line[0].remove()
            except TypeError:
                line.remove()
        self._handlers_annotations = []

    def remove_legend(self) -> None:
        """Remove the legend of the chart."""
        if self._legend is not None:
            self._legend.remove()
            self._legend = None

    def save(self, path_dest: Any, **params: Any) -> None:
        """Write the chart to disk."""
        if self._axes is None:
            self.plot()
        assert self._canvas is not None
        self._canvas.print_figure(path_dest, **params)
        gc.collect()

    def close_fig(self) -> None:
        """Close the figure plot."""
        if self._axes is not None:
            assert self._fig is not None
            self.remove_annotations()
            self.remove_legend()
            self._axes.remove()
            self._axes = None
            self._fig.clear()
            self._fig = None
            self._canvas = None
            gc.collect()
