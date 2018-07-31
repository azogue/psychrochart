# -*- coding: utf-8 -*-
"""A library to make psychrometric charts and overlay information in them."""
import gc
import json
from math import atan2, degrees

from matplotlib import patches, figure
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.legend import Legend  # NOQA
from matplotlib.path import Path, np
from typing import Iterable, List, Callable, Union, Dict, AnyStr, Any, Tuple
from typing import Optional  # NOQA
try:
    # noinspection PyPackageRequirements
    from scipy.spatial import ConvexHull
except ImportError:  # pragma: no cover
    ConvexHull = None

from psychrochart.equations import (
    PRESSURE_STD_ATM_KPA, pressure_by_altitude, humidity_ratio,
    specific_volume, dew_point_temperature, water_vapor_pressure,
    enthalpy_moist_air, saturation_pressure_water_vapor,
    dry_temperature_for_enthalpy_of_moist_air, relative_humidity_from_temps,
    dry_temperature_for_specific_volume_of_moist_air)
from psychrochart.util import (
    load_config, load_zones, mod_color, f_range, solve_curves_with_iteration)

PSYCHRO_CURVES_KEYS = [
    'constant_dry_temp_data', 'constant_humidity_data',
    'constant_h_data', 'constant_v_data', 'constant_rh_data',
    'constant_wbt_data', 'saturation']


def _between_limits(x_data: List[float], y_data: List[float],
                    xmin: float, xmax: float,
                    ymin: float, ymax: float) -> bool:
    data_xmin = min(x_data)
    data_xmax = max(x_data)
    data_ymin = min(y_data)
    data_ymax = max(y_data)
    if ((data_ymax < ymin) or (data_xmax < xmin) or
            (data_ymin > ymax) or (data_xmin > xmax)):
        return False
    return True


class PsychroCurve:
    """Object to store a psychrometric curve for plotting."""

    def __init__(self,
                 x_data: List[float]=None,
                 y_data: List[float]=None,
                 style: dict=None,
                 type_curve: str=None,
                 limits: dict=None,
                 label: str=None, label_loc: float=.75,
                 logger=None,
                 verbose: bool=False) -> None:
        """Create the Psychrocurve object."""
        self._logger = logger
        self._verbose = verbose
        self.x_data = x_data if x_data else []  # type: List[float]
        self.y_data = y_data if y_data else []  # type: List[float]
        self.style = style or {}  # type: dict
        self._type_curve = type_curve
        self._label = label
        self._label_loc = label_loc
        self._limits = limits
        self._is_patch = (style is not None
                          and 'facecolor' in style)  # type: bool

    def __bool__(self) -> bool:
        """Return the valid existence of the curve."""
        if self.x_data is not None and len(self.x_data) > 1 \
                and self.y_data is not None and len(self.y_data) > 1:
            return True
        return False

    def __repr__(self) -> str:
        """Object string representation."""
        name = 'PsychroZone' if self._is_patch else 'PsychroCurve'
        if self and self.x_data:
            return '<{} {} values (label: {})>'.format(
                name, len(self.x_data), self._label)
        else:
            return '<Empty {} (label: {})>'.format(name, self._label)

    def _print_err(self, *args):
        if self._logger is not None:  # pragma: no cover
            self._logger.error(*args)  # pragma: no cover
        elif self._verbose:  # pragma: no cover
            print(args[0] % args[1:])  # pragma: no cover

    def to_dict(self) -> Dict:
        """Return the curve as a dict."""
        if not self.x_data or not self.y_data:
            return {}
        return {
            "x_data": self.x_data,
            "y_data": self.y_data,
            "style": self.style,
            "label": self._label}

    def to_json(self) -> str:
        """Return the curve as a JSON string."""
        return json.dumps(self.to_dict())

    def from_json(self, json_str: AnyStr):
        """Load a curve from a JSON string."""
        data = json.loads(json_str)
        self.x_data = data['x_data']
        self.y_data = data['y_data']
        self.style = data.get('style')
        self._label = data.get('label')
        return self

    @staticmethod
    def _annotate_label(ax: Axes, label: AnyStr,
                        text_x: float, text_y: float, rotation: float,
                        text_style: Dict):
        if abs(rotation) > 0:
            text_loc = np.array((text_x, text_y))
            text_style['rotation'] = ax.transData.transform_angles(
                np.array((rotation,)), text_loc.reshape((1, 2)))[0]
            text_style['rotation_mode'] = 'anchor'
        ax.annotate(label, (text_x, text_y), **text_style)

    def plot(self, ax: Axes) -> Axes:
        """Plot the curve."""
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        if not self.x_data or not self.y_data or not _between_limits(
                self.x_data, self.y_data, xmin, xmax, ymin, ymax):
            self._print_err(
                '{} (label:{}) Not between limits ([{}, {}, {}, {}]) '
                '-> x:{}, y:{}'.format(
                    self._type_curve, self._label,
                    xmin, xmax, ymin, ymax, self.x_data, self.y_data))
            return ax

        if self._is_patch and self.y_data is not None:
            assert len(self.y_data) > 2
            verts = list(zip(self.x_data, self.y_data))
            codes = ([Path.MOVETO] + [Path.LINETO] * (len(self.y_data) - 2)
                     + [Path.CLOSEPOLY])
            path = Path(verts, codes)
            patch = patches.PathPatch(path, **self.style)
            ax.add_patch(patch)

            if self._label is not None:
                bbox_p = path.get_extents()
                text_x = .5 * (bbox_p.x0 + bbox_p.x1)
                text_y = .5 * (bbox_p.y0 + bbox_p.y1)
                style = {'ha': 'center', 'va': 'center',
                         "backgroundcolor": [1, 1, 1, .4]}
                if 'edgecolor' in self.style:
                    style['color'] = mod_color(self.style['edgecolor'], -25)
                self._annotate_label(ax, self._label,
                                     text_x, text_y, 0, style)
        else:
            ax.plot(self.x_data, self.y_data, **self.style)
            if self._label is not None:
                self.add_label(ax)

        return ax

    def add_label(self, ax: Axes,
                  text_label: str=None,
                  va: str=None, ha: str=None,
                  loc: float=None, **params) -> Axes:
        """Annotate the curve with its label."""
        num_samples = len(self.x_data)
        assert num_samples > 1
        text_style = {'va': 'bottom', 'ha': 'left', 'color': [0., 0., 0.]}
        loc_f = self._label_loc if loc is None else loc  # type: float
        label = ((self._label if self._label is not None else '')
                 if text_label is None else text_label)  # type: str

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
                text_y = (self.y_data[0]
                          + loc_f * (self.y_data[1] - self.y_data[0]))
            elif loc_f == 1.:
                if self.x_data[1] > xmax:
                    text_x = xmax
                    text_y = self.y_data[0] + tilt * (xmax - self.x_data[0])
                else:
                    text_x, text_y = self.x_data[1], self.y_data[1]
                label += '    '
                text_style['ha'] = 'right'
            else:
                text_x = self.x_data[0] + loc_f * (xmax - xmin)
                if text_x < xmin:
                    text_x = xmin + loc_f * (xmax - xmin)
                text_y = self.y_data[0] + tilt * (text_x - self.x_data[0])
        else:
            idx = min(num_samples - 2, int(num_samples * loc_f))
            rotation, tilt = _tilt_params(self.x_data, self.y_data,
                                          idx, idx + 1)
            text_x, text_y = self.x_data[idx], self.y_data[idx]
            text_style['ha'] = 'center'

        if 'color' in self.style:
            text_style['color'] = mod_color(self.style['color'], -25)
        if ha is not None:
            text_style['ha'] = ha
        if va is not None:
            text_style['va'] = va
        if params:
            text_style.update(params)

        self._annotate_label(ax, label, text_x, text_y, rotation, text_style)

        return ax


class PsychroCurves:
    """Object to store a list of psychrometric curves for plotting."""

    def __init__(self,
                 curves: List[PsychroCurve],
                 family_label: str=None) -> None:
        """Create the Psychrocurves array object."""
        self.curves = curves  # type: List[PsychroCurve]
        self.size = len(self.curves)  # type: int
        self.family_label = family_label  # type: Optional[str]

    # def __len__(self) -> int:
    #     """Return the # of curves."""
    #     return self.size

    # def __sizeof__(self) -> int:
    #     """Return the # of curves."""
    #     return self.size

    def __getitem__(self, item) -> PsychroCurve:
        """Get item from the PsychroCurve list."""
        return self.curves[item]

    def __repr__(self) -> str:
        """Object string representation."""
        return '<{} PsychroCurves (label: {})>'.format(
            self.size, self.family_label)

    def plot(self, ax: Axes) -> Axes:
        """Plot the family curves."""
        [curve.plot(ax) for curve in self.curves]

        # Curves family labelling
        if self.curves and self.family_label is not None:
            style = self.curves[0].style or {}
            ax.plot([-1], [-1], label=self.family_label,
                    marker='D', markersize=10, **style)

        return ax


def _gen_list_curves_range_temps(
        func_curve: Callable,
        dbt_min: float, dbt_max: float, increment: float,
        curves_values: list,
        p_atm_kpa: float=PRESSURE_STD_ATM_KPA) -> Tuple[List[float],
                                                        List[List[float]]]:
    """Generate a curve from a range of temperatures."""
    temps = f_range(dbt_min, dbt_max + increment, increment)
    curves = [func_curve(temps, value, p_atm_kpa) for value in curves_values]
    return temps, curves


def curve_constant_humidity_ratio(
        dry_temps: List[float], rh_percentage: float=100.,
        p_atm_kpa: float=PRESSURE_STD_ATM_KPA, mode_sat=1) -> List[float]:
    """Generate a curve (numpy array) of constant humidity ratio."""
    return [1000 * humidity_ratio(
        saturation_pressure_water_vapor(t, mode=mode_sat)
        * rh_percentage / 100., p_atm_kpa)
            for t in dry_temps]


def _make_zone_dbt_rh(
        t_min: float, t_max: float, increment: float,
        rh_min: float, rh_max: float,
        p_atm_kpa: float=PRESSURE_STD_ATM_KPA,
        style: dict=None,
        label: str=None,
        logger=None) -> PsychroCurve:
    """Generate points for zone between constant dry bulb temps and RH."""
    temps = f_range(t_min, t_max + increment, increment)
    curve_rh_up = curve_constant_humidity_ratio(temps, rh_max, p_atm_kpa)
    curve_rh_down = curve_constant_humidity_ratio(temps, rh_min, p_atm_kpa)
    abs_humid = (curve_rh_up + curve_rh_down[::-1]
                 + [curve_rh_up[0]])  # type: List[float]
    temps_zone = temps + temps[::-1] + [temps[0]]  # type: List[float]
    return PsychroCurve(temps_zone, abs_humid, style,
                        type_curve='constant_rh_data', label=label,
                        logger=logger)


def _valid_zone_type(zone_type: str) -> bool:
    """Implemented zone types."""
    if zone_type in ['dbt-rh', 'xy-points']:
        return True
    return False


def _make_zone(
        zone_conf: Dict, increment: float,
        p_atm_kpa: float=PRESSURE_STD_ATM_KPA,
        logger=None) -> PsychroCurve:
    """Generate points for zone between constant dry bulb temps and RH."""
    if zone_conf['zone_type'] == 'dbt-rh':
        t_min, t_max = zone_conf['points_x']
        rh_min, rh_max = zone_conf['points_y']
        return _make_zone_dbt_rh(
            t_min, t_max, increment, rh_min, rh_max, p_atm_kpa,
            zone_conf['style'], label=zone_conf.get('label'), logger=logger)
    # elif zone_conf['zone_type'] == 'xy-points':
    else:
        return PsychroCurve(
            zone_conf['points_x'], zone_conf['points_y'], zone_conf['style'],
            type_curve='custom path', label=zone_conf.get('label'),
            logger=logger)
    # elif zone_conf['zone_type'] == 'dbt-rh-points':
    # make conversion rh -> w


class PsychroChart:
    """Psychrometric chart object handler."""

    def __init__(self,
                 styles: Union[dict, str]=None,
                 zones_file: Union[dict, str]=None,
                 logger: Any=None,
                 verbose: bool=False) -> None:
        """Create the PsychroChart object."""
        self._logger = logger
        self._verbose = verbose
        self.d_config = {}  # type: dict
        self.figure_params = {}  # type: dict
        self.dbt_min = self.dbt_max = -100
        self.w_min = self.w_max = -1
        self.temp_step = 1.
        self.altitude_m = -1
        self.chart_params = {}  # type: dict
        self.p_atm_kpa = PRESSURE_STD_ATM_KPA
        self.constant_dry_temp_data = None  # type: Optional[PsychroCurves]
        self.constant_humidity_data = None  # type: Optional[PsychroCurves]
        self.constant_rh_data = None  # type: Optional[PsychroCurves]
        self.constant_h_data = None  # type: Optional[PsychroCurves]
        self.constant_v_data = None  # type: Optional[PsychroCurves]
        self.constant_wbt_data = None  # type: Optional[PsychroCurves]
        self.saturation = None  # type: Optional[PsychroCurves]
        self.zones = []  # type: List

        self._fig = None  # type: figure.Figure
        self._canvas = None  # type: FigureCanvas
        self._axes = None  # type: Axes
        self._legend = None  # type: Legend
        self._handlers_annotations = []  # type: List

        self._make_chart_data(styles, zones_file)

    def __repr__(self) -> str:
        """Return a string representation of the PsychroChart object."""
        return '<PsychroChart [{:g}->{:g} °C, {:g}->{:g} gr/kg_da]>'.format(
            self.dbt_min, self.dbt_max, self.w_min, self.w_max)

    @property
    def axes(self) -> Axes:
        """Return the Axes object plotting the chart if necessary."""
        if self._axes is None:
            self.plot()
        assert isinstance(self._axes, Axes)
        return self._axes

    def _make_chart_data(self,
                         styles: Union[dict, str]=None,
                         zones_file: Union[dict, str]=None) -> None:
        """Generate the data to plot the psychrometric chart."""
        # Get styling
        config = load_config(styles)
        self.d_config = config
        self.temp_step = config['limits']['step_temp']

        self.figure_params = config['figure']
        self.dbt_min, self.dbt_max = config['limits']['range_temp_c']
        self.w_min, self.w_max = config['limits']['range_humidity_g_kg']
        self.chart_params = config['chart_params']

        # Base pressure
        if config['limits'].get('pressure_kpa') is not None:
            self.p_atm_kpa = config['limits']['pressure_kpa']
        elif config['limits'].get('altitude_m') is not None:
            self.altitude_m = config['limits']['altitude_m']
            self.p_atm_kpa = pressure_by_altitude(self.altitude_m)

        # Dry bulb constant lines (vertical):
        if self.chart_params["with_constant_dry_temp"]:
            step = self.chart_params["constant_temp_step"]
            style = config['constant_dry_temp']
            temps_vl = f_range(self.dbt_min, self.dbt_max, step)
            heights = [1000 * humidity_ratio(
                saturation_pressure_water_vapor(t),
                p_atm_kpa=self.p_atm_kpa) for t in temps_vl]

            self.constant_dry_temp_data = PsychroCurves(
                [PsychroCurve([t, t], [self.w_min, h], style,
                              type_curve='constant_dry_temp_data',
                              label=None, logger=self._logger)
                 for t, h in zip(temps_vl, heights)],
                family_label=self.chart_params["constant_temp_label"])

        # Absolute humidity constant lines (horizontal):
        if self.chart_params["with_constant_humidity"]:
            step = self.chart_params["constant_humid_step"]
            style = config['constant_humidity']
            ws_hl = f_range(self.w_min + step, self.w_max + step / 10, step)
            dew_points = solve_curves_with_iteration(
                'DEW POINT', [x / 1000 for x in ws_hl],
                lambda x: dew_point_temperature(
                        water_vapor_pressure(
                            x, p_atm_kpa=self.p_atm_kpa)),
                lambda x: humidity_ratio(
                    saturation_pressure_water_vapor(x),
                    p_atm_kpa=self.p_atm_kpa))

            self.constant_humidity_data = PsychroCurves(
                [PsychroCurve([t_dp, self.dbt_max], [w, w], style,
                              type_curve='constant_humidity_data',
                              label=None, logger=self._logger)
                 for w, t_dp in zip(ws_hl, dew_points)],
                family_label=self.chart_params["constant_humid_label"])

        # Constant relative humidity curves:
        if self.chart_params["with_constant_rh"]:
            rh_perc_values = self.chart_params["constant_rh_curves"]
            rh_label_values = self.chart_params.get("constant_rh_labels", [])
            label_loc = self.chart_params.get("constant_rh_labels_loc", .85)
            style = config["constant_rh"]
            temps_ct_rh, curves_ct_rh = _gen_list_curves_range_temps(
                curve_constant_humidity_ratio,
                self.dbt_min, self.dbt_max, self.temp_step,
                rh_perc_values, p_atm_kpa=self.p_atm_kpa)

            self.constant_rh_data = PsychroCurves(
                [PsychroCurve(
                    temps_ct_rh, curve_ct_rh, style,
                    type_curve='constant_rh_data',
                    label_loc=label_loc, label='RH {:g} %'.format(rh)
                    if round(rh, 1) in rh_label_values else None,
                    logger=self._logger)
                    for rh, curve_ct_rh in zip(rh_perc_values, curves_ct_rh)],
                family_label=self.chart_params["constant_rh_label"])

        # Constant enthalpy lines:
        if self.chart_params["with_constant_h"]:
            step = self.chart_params["constant_h_step"]
            start, end = self.chart_params["range_h"]
            enthalpy_values = f_range(start, end, step)
            h_label_values = self.chart_params.get("constant_h_labels", [])
            label_loc = self.chart_params.get("constant_h_labels_loc", 1.)
            style = config["constant_h"]
            temps_max_constant_h = [
                dry_temperature_for_enthalpy_of_moist_air(
                    self.w_min / 1000, h)
                for h in enthalpy_values]

            sat_points = solve_curves_with_iteration(
                'ENTHALPHY', enthalpy_values,
                lambda x: dry_temperature_for_enthalpy_of_moist_air(
                    self.w_min / 1000 + 0.1, x),
                lambda x: enthalpy_moist_air(
                    x, saturation_pressure_water_vapor(x),
                    p_atm_kpa=self.p_atm_kpa))

            self.constant_h_data = PsychroCurves(
                [PsychroCurve(
                    [t_sat, t_max], [1000 * humidity_ratio(
                        saturation_pressure_water_vapor(t_sat),
                        self.p_atm_kpa), self.w_min], style,
                    type_curve='constant_h_data',
                    label_loc=label_loc, label='{:g} kJ/kg_da'.format(h)
                    if round(h, 3) in h_label_values else None,
                    logger=self._logger)
                    for t_sat, t_max, h in zip(
                    sat_points, temps_max_constant_h, enthalpy_values)],
                family_label=self.chart_params["constant_h_label"])

        # Constant specific volume lines:
        if self.chart_params["with_constant_v"]:
            step = self.chart_params["constant_v_step"]
            start, end = self.chart_params["range_vol_m3_kg"]
            vol_values = f_range(start, end, step)
            vol_label_values = self.chart_params.get("constant_v_labels", [])
            label_loc = self.chart_params.get("constant_v_labels_loc", 1.)
            style = config["constant_v"]
            temps_max_constant_v = [
                dry_temperature_for_specific_volume_of_moist_air(
                    0, specific_vol, p_atm_kpa=self.p_atm_kpa)
                for specific_vol in vol_values]
            sat_points = solve_curves_with_iteration(
                'CONSTANT VOLUME', vol_values,
                lambda x: dry_temperature_for_specific_volume_of_moist_air(
                    0, x, p_atm_kpa=self.p_atm_kpa),
                lambda x: specific_volume(
                    x, saturation_pressure_water_vapor(x),
                    p_atm_kpa=self.p_atm_kpa))

            self.constant_v_data = PsychroCurves(
                [PsychroCurve(
                    [t_sat, t_max], [1000 * humidity_ratio(
                        saturation_pressure_water_vapor(t_sat),
                        self.p_atm_kpa), 0],
                    style, type_curve='constant_v_data',
                    label_loc=label_loc, label='{:g} m3/kg_da'.format(vol)
                    if round(vol, 3) in vol_label_values else None,
                    logger=self._logger)
                    for t_sat, t_max, vol in zip(
                    sat_points, temps_max_constant_v, vol_values)],
                family_label=self.chart_params["constant_v_label"])

        # Constant wet bulb temperature lines:
        if self.chart_params["with_constant_wet_temp"]:
            step = self.chart_params["constant_wet_temp_step"]
            start, end = self.chart_params["range_wet_temp"]
            wbt_values = f_range(start, end, step)
            wbt_label_values = self.chart_params.get(
                "constant_wet_temp_labels", [])
            label_loc = self.chart_params.get(
                "constant_wet_temp_labels_loc", .05)
            style = config["constant_wet_temp"]
            w_max_constant_wbt = [humidity_ratio(
                saturation_pressure_water_vapor(wbt), self.p_atm_kpa)
                for wbt in wbt_values]

            self.constant_wbt_data = PsychroCurves(
                [PsychroCurve(
                    [wbt, self.dbt_max],
                    [1000 * w_max,
                     1000 * humidity_ratio(
                         saturation_pressure_water_vapor(self.dbt_max)
                         * relative_humidity_from_temps(
                             self.dbt_max, wbt, p_atm_kpa=self.p_atm_kpa),
                         p_atm_kpa=self.p_atm_kpa)], style,
                    type_curve='constant_wbt_data',
                    label_loc=label_loc, label='{:g} °C'.format(wbt)
                    if wbt in wbt_label_values else None, logger=self._logger)
                    for wbt, w_max in zip(wbt_values, w_max_constant_wbt)],
                family_label=self.chart_params["constant_wet_temp_label"])

        # Saturation line:
        if True:
            sat_style = config["saturation"]
            temps_sat_line, w_sat_line = _gen_list_curves_range_temps(
                curve_constant_humidity_ratio,
                self.dbt_min, self.dbt_max, self.temp_step, [100],
                p_atm_kpa=self.p_atm_kpa)

            self.saturation = PsychroCurves(
                [PsychroCurve(
                    temps_sat_line, w_sat_line[0], sat_style,
                    type_curve='saturation', logger=self._logger)])

        # Zones
        if self.chart_params["with_zones"] or zones_file is not None:
            self.append_zones(zones_file)

    def append_zones(self, zones: Union[dict, str]=None) -> None:
        """Append zones as patches to the psychrometric chart."""
        if zones is None:
            # load default 'Comfort' zones (Spain RITE)
            d_zones = load_zones()
        else:
            d_zones = load_zones(zones)

        zones_ok = [_make_zone(
            zone_conf, self.temp_step, self.p_atm_kpa, logger=self._logger)
            for zone_conf in d_zones['zones']
            if _valid_zone_type(zone_conf['zone_type'])]
        if zones_ok:
            self.zones.append(PsychroCurves(zones_ok))

    def plot_points_dbt_rh(self,
                           points: Dict,
                           connectors: list=None,
                           convex_groups: list=None) -> Dict:
        """Append individual points, connectors and groups to the plot.

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
        # Or, with default style:
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
        points_plot = {}
        default_style = {'marker': 'o', 'markersize': 10,
                         'color': [1, .8, 0.1, .8], 'linewidth': 0}
        for key, point in points.items():
            plot_params = default_style.copy()
            if isinstance(point, dict):
                plot_params.update(point.get('style', {}))
                plot_params['label'] = point.get('label')
                point = point['xy']
            temp = point[0]
            w_g_ka = curve_constant_humidity_ratio(
                [temp], rh_percentage=point[1], p_atm_kpa=self.p_atm_kpa)[0]
            points_plot[key] = [temp], [w_g_ka], plot_params

        if connectors is not None:
            for i, d_con in enumerate(connectors):
                if (d_con['start'] in points_plot and
                        d_con['end'] in points_plot):
                    x_start = points_plot[d_con['start']][0][0]
                    y_start = points_plot[d_con['start']][1][0]
                    x_end = points_plot[d_con['end']][0][0]
                    y_end = points_plot[d_con['end']][1][0]
                    x_line = [x_start, x_end]
                    y_line = [y_start, y_end]
                    style = d_con.get('style', points_plot[d_con['start']][2])
                    self._handlers_annotations.append(
                        self.axes.plot(
                            x_line, y_line, dash_capstyle='round', **style))
                    self._handlers_annotations.append(
                        self.axes.plot(
                            x_line, y_line,
                            color=list(style['color'][:3]) + [.15],
                            lw=50, solid_capstyle='round'))
        
        # MODIFICATION - JW
        # Create lists for x and y coords
        x = []; y=[]

        for point in points_plot.values():
            # Added this for some debug
            # count += 1
            # if count % 1000 == 0:
            #     print('{} points out of {} complete'.format(count, len(points_plot.values())))

            #Generate the x, y list for the scatter plot
            x.append(point[0])
            y.append(point[1])  
            # self._handlers_annotations.append(
            #     self.axes.plot(point[0], point[1], **point[2]))

        # Use scatter instead of plt
        self._handlers_annotations.append(
                self.axes.scatter(x, y))

        # ORIGINAL CODE
        # for point in points_plot.values():
        #     self._handlers_annotations.append(
        #         self.axes.plot(point[0], point[1], **point[2]))
        # END OF ORIGINAL CODE
        
        # END OF MODIFICATION
        
        if (ConvexHull is not None
                and convex_groups and points_plot and
                (isinstance(convex_groups[0], list) or
                 isinstance(convex_groups[0], tuple))
                and len(convex_groups[0]) == 3):
            for convex_hull_zone, style_line, style_fill in convex_groups:
                int_points = np.array(
                    [(point[0][0], point[1][0])
                     for name, point in points_plot.items()
                     if name in convex_hull_zone])

                if len(int_points) < 3:
                    continue

                hull = ConvexHull(int_points)
                # noinspection PyUnresolvedReferences
                for simplex in hull.simplices:
                    self._handlers_annotations.append(
                        self.axes.plot(int_points[simplex, 0],
                                       int_points[simplex, 1], **style_line))
                self._handlers_annotations.append(
                    self.axes.fill(int_points[hull.vertices, 0],
                                   int_points[hull.vertices, 1], **style_fill))

        return points_plot

    def plot_arrows_dbt_rh(self, points_pairs: Dict) -> Dict:
        """Append individual points to the plot."""
        points_plot = {}
        default_style = {
            "linewidth": 0,
            "color": [1, .8, 0.1, .8],
            "arrowstyle": 'wedge'}
        for key, pair_point in points_pairs.items():
            plot_params = default_style.copy()
            if isinstance(pair_point, dict):
                if 'style' in pair_point and "color" in pair_point['style']:
                    plot_params['color'] = mod_color(
                        pair_point['style']['color'], .6)  # set alpha
                point1, point2 = pair_point['xy']
            else:
                point1, point2 = pair_point
            temp1 = point1[0]
            temp2 = point2[0]
            w_g_ka1 = curve_constant_humidity_ratio(
                [temp1], rh_percentage=point1[1], p_atm_kpa=self.p_atm_kpa)[0]
            w_g_ka2 = curve_constant_humidity_ratio(
                [temp2], rh_percentage=point2[1], p_atm_kpa=self.p_atm_kpa)[0]

            self._handlers_annotations.append(
                self.axes.annotate(
                    '', (temp2, w_g_ka2), xytext=(temp1, w_g_ka1),
                    arrowprops=plot_params))

            points_plot[key] = (temp1, w_g_ka1), (temp2, w_g_ka2), plot_params

        return points_plot

    def plot_vertical_dry_bulb_temp_line(
            self, temp: float,
            style: dict=None,
            label: str=None,
            reverse: bool=False,
            **label_params) -> None:
        """Append a vertical line from w_min to w_sat."""
        w_max = 1000 * humidity_ratio(
            saturation_pressure_water_vapor(temp), self.p_atm_kpa)

        style_curve = style or self.d_config.get("constant_dry_temp")
        path_y = [w_max, self.w_min] if reverse else [self.w_min, w_max]
        curve = PsychroCurve(
            [temp, temp], path_y, style=style_curve, logger=self._logger)
        curve.plot(self.axes)
        if label is not None:
            curve.add_label(self.axes, label, **label_params)

    def plot_legend(
            self, loc: str='upper left', markerscale: float=.9,
            frameon: bool=True, fancybox: bool=True,
            edgecolor: Union[str, Iterable]='darkgrey', fontsize: float=15.,
            labelspacing: float=1.5, **params) -> None:
        """Append a legend to the psychrochart plot."""
        self._legend = self.axes.legend(
            loc=loc, markerscale=markerscale, frameon=frameon,
            edgecolor=edgecolor, fontsize=fontsize, fancybox=fancybox,
            labelspacing=labelspacing, **params)

    def plot(self, ax: Axes=None) -> Axes:
        """Plot the psychrochart and return the matplotlib Axes instance."""
        def _apply_spines_style(axes, style, location='right'):
            for key in style:
                if (key == 'color') or (key == 'c'):
                    axes.spines[location].set_color(style[key])
                elif (key == 'linewidth') or (key == 'lw'):
                    axes.spines[location].set_linewidth(style[key])
                elif (key == 'linestyle') or (key == 'ls'):
                    axes.spines[location].set_linestyle(style[key])
                else:  # pragma: no cover
                    try:
                        getattr(axes.spines[location],
                                'set_{}'.format(key))(style[key])
                    except Exception as exc:
                        self._print_err(
                            "Error trying to apply spines attrs: %s. (%s)",
                            exc, dir(axes.spines[location]))

        # Prepare fig & axis
        fig_params = self.figure_params.copy()
        figsize = fig_params.pop('figsize', (16, 9))
        position = fig_params.pop('position', [0.025, 0.075, 0.925, 0.875])
        fontsize = fig_params.pop('fontsize', 10)
        x_style = fig_params.pop('x_axis', {})
        x_style_labels = fig_params.pop('x_axis_labels', {})
        x_style_ticks = fig_params.pop('x_axis_ticks', {})
        y_style = fig_params.pop('y_axis', {})
        y_style_labels = fig_params.pop('y_axis_labels', {})
        y_style_ticks = fig_params.pop('y_axis_ticks', {})
        partial_axis = fig_params.pop('partial_axis', True)

        # Create figure and format axis
        self._fig = figure.Figure(figsize=figsize, dpi=150, frameon=False)
        self._canvas = FigureCanvas(self._fig)
        if ax is None:
            ax = self._fig.gca(position=position)
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")
        ax.set_xlim(self.dbt_min, self.dbt_max)
        ax.set_ylim(self.w_min, self.w_max)
        ax.grid(False, which='major', axis='both')
        ax.grid(False, which='minor', axis='both')

        # Apply axis styles
        if fig_params['x_label'] is not None:
            style_axis = x_style_labels.copy()
            style_axis['fontsize'] *= 1.2
            ax.set_xlabel(fig_params['x_label'], **style_axis)
        if fig_params['y_label'] is not None:
            style_axis = y_style_labels.copy()
            style_axis['fontsize'] *= 1.2
            ax.set_ylabel(fig_params['y_label'], **style_axis)
        if fig_params['title'] is not None:
            ax.set_title(fig_params['title'],
                         fontsize=fontsize * 1.5, fontweight='bold')

        _apply_spines_style(ax, y_style, location='right')
        _apply_spines_style(ax, x_style, location='bottom')
        if partial_axis:  # Hide left and top axis
            ax.spines['left'].set_visible(False)
            ax.spines['top'].set_visible(False)
        else:
            _apply_spines_style(ax, y_style, location='left')
            _apply_spines_style(ax, x_style, location='top')

        if x_style_ticks:
            ax.tick_params(axis='x', **x_style_ticks)
        if y_style_ticks:
            ax.tick_params(axis='y', **y_style_ticks)

        if self.chart_params.get("with_constant_dry_temp", True):
            step_label = self.chart_params.get(
                "constant_temp_label_step", None)
            if step_label:  # Explicit xticks
                ticks = f_range(self.dbt_min, self.dbt_max + step_label / 10,
                                step_label)
                if not self.chart_params.get(
                        "constant_temp_label_include_limits", True):
                    ticks = [t for t in ticks
                             if t not in [self.dbt_min, self.dbt_max]]
                ax.set_xticks(ticks)
                ax.set_xticklabels(
                    ['{:g}'.format(t) for t in ticks], **x_style_labels)
        else:
            ax.set_xticks([])

        if self.chart_params.get("with_constant_humidity", True):
            step_label = self.chart_params.get(
                "constant_humid_label_step", None)
            if step_label:  # Explicit xticks
                ticks = f_range(self.w_min, self.w_max + step_label / 10,
                                step_label)
                if not self.chart_params.get(
                        "constant_humid_label_include_limits", True):
                    ticks = [t for t in ticks
                             if t not in [self.w_min, self.w_max]]
                ax.set_yticks(ticks)
                ax.set_yticklabels(
                    ['{:g}'.format(t) for t in ticks], **y_style_labels)
        else:
            ax.set_yticks([])

        # Plot curves:
        [getattr(self, curve_family).plot(ax)
         for curve_family in PSYCHRO_CURVES_KEYS
         if getattr(self, curve_family) is not None]

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
        self._canvas.print_figure(path_dest, **params)
        gc.collect()

    def close_fig(self) -> None:
        """Close the figure plot."""
        if self._axes is not None:
            self.remove_annotations()
            self.remove_legend()
            self._axes.remove()
            self._axes = None
            self._fig.clear()
            self._fig = None
            self._canvas = None
            gc.collect()

    def _print_err(self, *args: Any) -> None:
        if self._logger is not None:  # pragma: no cover
            self._logger.error(*args)  # pragma: no cover
        elif self._verbose:  # pragma: no cover
            print(args[0] % args[1:])  # pragma: no cover
