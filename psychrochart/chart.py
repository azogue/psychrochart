"""A library to make psychrometric charts and overlay information in them."""
import gc
from io import StringIO
from pathlib import Path
from typing import Any, Iterable, Type

from matplotlib import figure
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.backend_bases import FigureCanvasBase
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.legend import Legend

from psychrochart.chartdata import (
    gen_points_in_constant_relative_humidity,
    make_constant_dry_bulb_v_line,
)
from psychrochart.models.annots import ChartAnnots, ChartZones
from psychrochart.models.config import ChartConfig
from psychrochart.models.curves import PsychroChartModel
from psychrochart.models.parsers import (
    ConvexGroupTuple,
    load_extra_annots,
    load_points_dbt_rh,
    obj_loader,
)
from psychrochart.models.styles import CurveStyle
from psychrochart.plot_logic import (
    add_label_to_curve,
    apply_axis_styling,
    plot_annots_dbt_rh,
    plot_chart,
    plot_curve,
)
from psychrochart.process_logic import (
    append_zones_to_chart,
    generate_psychrochart,
    update_psychrochart_data,
)
from psychrochart.util import mod_color


def _select_fig_canvas(
    path_dest: Any, canvas_cls: Type[FigureCanvasBase] | None = None
) -> Type[FigureCanvasBase]:
    if (
        canvas_cls is None
        and isinstance(path_dest, (str, Path))
        and str(path_dest).endswith(".svg")
    ):
        canvas_cls = FigureCanvasSVG
    elif canvas_cls is None:
        canvas_cls = FigureCanvasAgg
    return canvas_cls


class PsychroChart(PsychroChartModel):
    """Psychrometric chart object handler."""

    config: ChartConfig
    _fig: figure.Figure | None = None
    _axes: Axes | None = None
    _legend: Legend | None = None
    _handlers_annotations: list[Artist | list[Artist]]

    class Config:
        arbitrary_types_allowed = True
        underscore_attrs_are_private = True

    def _init_private_attributes(self) -> None:
        self._handlers_annotations = []
        super()._init_private_attributes()

    @classmethod
    def create(
        cls,
        config: ChartConfig | dict[str, Any] | str | None = None,
        *,
        extra_zones: ChartZones | dict[str, Any] | str | None = None,
        use_unit_system_si: bool = True,
    ):
        chart_config = obj_loader(ChartConfig, config)
        chart_config.commit_changes()
        chart_data = generate_psychrochart(
            chart_config, extra_zones, use_unit_system_si
        )
        chart = cls(config=chart_config, **chart_data.dict())
        return chart

    def __repr__(self) -> str:
        """Return a string representation of the PsychroChart object."""
        return (
            f"<PsychroChart [{self.config.dbt_min:g}"
            f"->{self.config.dbt_max:g} °C, "
            f"{self.config.w_min:g}"
            f"->{self.config.w_max:g} gr/kg_da]>"
        )

    def _ensure_updated_data(self):
        if self.config.has_changed:
            update_psychrochart_data(self, self.config)

    @property
    def axes(self) -> Axes:
        """Return the Axes object plotting the chart if necessary."""
        self._ensure_updated_data()
        if self._axes is None:
            self.plot()
        assert isinstance(self._axes, Axes)
        return self._axes

    def append_zones(
        self, zones: ChartZones | dict[str, Any] | str | None = None
    ) -> None:
        """Append zones as patches to the psychrometric chart."""
        append_zones_to_chart(self.config, self, zones)

    def plot_points_dbt_rh(
        self,
        points: dict[str, Any],
        connectors: list[dict[str, Any]] | None = None,
        convex_groups: list[dict[str, Any]]
        | list[ConvexGroupTuple]
        | None = None,
        scatter_style: dict[str, Any] | None = None,
    ) -> ChartAnnots:
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
        data_points, data_series = load_points_dbt_rh(
            points, self.pressure, scatter_style
        )
        data_lines, data_areas = load_extra_annots(connectors, convex_groups)
        annots = ChartAnnots(
            points=data_points,
            series=data_series,
            connectors=data_lines,
            areas=data_areas,
            use_scatter=scatter_style is not None,
        )
        self._handlers_annotations.extend(
            plot_annots_dbt_rh(self.axes, annots)
        )
        return annots

    def plot_arrows_dbt_rh(
        self, points_pairs: dict[str, Any]
    ) -> dict[str, Any]:
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
        style: CurveStyle | dict[str, Any] | None = None,
        label: str | None = None,
        reverse: bool = False,
        **label_params,
    ) -> None:
        """Append a vertical line from w_min to w_sat."""
        style_curve = obj_loader(
            CurveStyle, style, default_obj=self.config.constant_dry_temp
        )
        curve = make_constant_dry_bulb_v_line(
            self.config.w_min,
            temp,
            self.pressure,
            style=style_curve,
            type_curve="constant-dbt",
            reverse=reverse,
        )

        if plot_curve(curve, self.axes) and label is not None:
            add_label_to_curve(curve, self.axes, label, **label_params)

    def plot_legend(
        self,
        loc: str = "upper left",
        markerscale: float = 0.9,
        frameon: bool = True,
        fancybox: bool = True,
        edgecolor: str | Iterable = "darkgrey",
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

    def plot(self, ax: Axes | None = None) -> Axes:
        """Plot the psychrochart and return the matplotlib Axes instance."""
        self._ensure_updated_data()
        if ax is not None:
            self._fig = ax.get_figure()
        else:
            self._fig = figure.Figure(
                figsize=self.config.figure.figsize,
                dpi=self.config.figure.dpi,
                frameon=False,
            )
            ax = self._fig.add_subplot(position=self.config.figure.position)
        self._axes = ax
        apply_axis_styling(self.config, self._axes)
        return plot_chart(self, self._axes)

    def remove_annotations(self) -> None:
        """Remove the annotations made in the chart to reuse it."""
        for line in self._handlers_annotations:
            if isinstance(line, list):
                line[0].remove()
            else:
                line.remove()
        self._handlers_annotations = []

    def remove_legend(self) -> None:
        """Remove the legend of the chart."""
        if self._legend is not None:
            self._legend.remove()
            self._legend = None

    def save(
        self,
        path_dest: Any,
        canvas_cls: Type[FigureCanvasBase] | None = None,
        **params,
    ) -> None:
        """Write the chart to disk."""
        # ensure destination path if folder does not exist
        if (
            isinstance(path_dest, (str, Path))
            and not Path(path_dest).parent.exists()
        ):
            Path(path_dest).parent.mkdir(parents=True)
        if self._axes is None or self.config.has_changed:
            self.plot()
        assert self._fig is not None
        canvas_use = _select_fig_canvas(path_dest, canvas_cls)
        canvas_use(self._fig).print_figure(path_dest, **params)
        gc.collect()

    def make_svg(self, **params) -> str:
        """Generate chart as SVG and return as text."""
        svg_io = StringIO()
        self.save(svg_io, canvas_cls=FigureCanvasSVG, **params)
        svg_io.seek(0)
        return svg_io.read()

    def close_fig(self) -> None:
        """Close the figure plot."""
        assert self._axes is not None
        assert self._fig is not None
        self.remove_annotations()
        self.remove_legend()
        self._axes.remove()
        self._axes = None
        self._fig.clear()
        self._fig = None
        gc.collect()
