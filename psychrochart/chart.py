# -*- coding: utf-8 -*-
"""
A python library to make psychrometric charts and overlay information in them.

"""
import json
from math import atan2, degrees
from matplotlib.axes import Axes
import matplotlib.patches as patches
from matplotlib.path import Path
import matplotlib.pyplot as plt
import numpy as np
from typing import Iterable, Callable, Union

from psychrochart.equations import (
    PRESSURE_STD_ATM_KPA, pressure_by_altitude, humidity_ratio,
    specific_volume, dew_point_temperature, water_vapor_pressure,
    enthalpy_moist_air, saturation_pressure_water_vapor,
    dry_temperature_for_enthalpy_of_moist_air, relative_humidity_from_temps,
    dry_temperature_for_specific_volume_of_moist_air
)
from psychrochart.util import load_config, load_zones, iter_solver, timeit
from psychrochart.styling import mod_color


PSYCHRO_CURVES_KEYS = [
    'constant_dry_temp_data', 'constant_humidity_data',
    'constant_h_data', 'constant_v_data', 'constant_rh_data',
    'constant_wbt_data', 'saturation']


def _between_limits(x_data, y_data, xmin, xmax, ymin, ymax):
    # TODO validate between limits in data creation!
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
                 x_data: np.array=None,
                 y_data: np.array=None,
                 style: dict=None,
                 type_curve: str=None,
                 limits: dict=None,
                 label: str=None, label_loc: float=.75):
        self.x_data = x_data
        self.y_data = y_data
        self.style = style or {}
        self._type_curve = type_curve
        self._label = label
        self._label_loc = label_loc
        self._limits = limits
        self._is_patch = style is not None and 'facecolor' in style

    def __dict__(self) -> dict:
        """Return the curve as a dict."""
        return {
            "x_data": self.x_data,
            "y_data": self.y_data,
            "style": self.style,
            "label": self._label}

    def __bool__(self):
        """Return the valid existence of the curve."""
        if self.x_data is not None and len(self.x_data) > 1 \
                and self.y_data is not None and len(self.y_data) > 1:
            return True
        return False

    def __repr__(self):
        """Object string representation."""
        name = 'PsychroZone' if self._is_patch else 'PsychroCurve'
        if self:
            return '<{} {} values (label: {})>'.format(
                name, len(self.x_data), self._label)
        else:
            return '<Empty {} (label: {})>'.format(name, self._label)

    def to_json(self) -> str:
        """Return the curve as a JSON string."""
        data = self.__dict__()
        data['x_data'] = data['x_data'].tolist()
        data['y_data'] = data['y_data'].tolist()
        return json.dumps(data)

    def from_json(self, json_str: str):
        """Load a curve from a JSON string."""
        data = json.loads(json_str)
        self.x_data = np.array(data['x_data'])
        self.y_data = np.array(data['y_data'])
        self.style = data.get('style')
        self._label = data.get('label')
        return self

    def plot(self, ax: Axes=None):
        """Plot the curve."""
        if ax is None:
            ax = plt.gca()

        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        if not _between_limits(self.x_data, self.y_data,
                               xmin, xmax, ymin, ymax):
            print('{} Not between limits ([{}, {}, {}, {}]) -> x:{}, y:{}'
                  .format(self._type_curve, xmin, xmax, ymin, ymax,
                          self.x_data, self.y_data))
            return ax

        if self._is_patch:
            assert len(self.y_data) > 2
            verts = list(zip(self.x_data, self.y_data))
            codes = ([Path.MOVETO] + [Path.LINETO] * (len(self.y_data) - 2)
                     + [Path.CLOSEPOLY])
            path = Path(verts, codes)
            patch = patches.PathPatch(path, **self.style)

            ax.add_patch(patch)
        else:
            ax.plot(self.x_data, self.y_data, **self.style)

        # Labelling
        if not self._is_patch and self._label is not None:
            self.add_label(ax)

        return ax

    def add_label(self, ax: Axes=None,
                  text_label: str=None,
                  va: str=None, ha: str=None, loc: float=None):
        """Annotate the curve with its label."""
        num_samples = len(self.x_data)
        assert num_samples > 1
        text_style = {'va': 'bottom', 'ha': 'left'}
        loc_f = self._label_loc if loc is None else loc
        label = self._label if text_label is None else text_label

        def _tilt_params(x_data, y_data, idx_0, idx_f):
            delta_x = x_data[idx_f] - self.x_data[idx_0]
            delta_y = y_data[idx_f] - self.y_data[idx_0]
            if delta_x == 0:
                rotation_deg = 90  # up to bottom
                tilt_curve = 1e12
            else:
                rotation_deg = degrees(atan2(delta_y, delta_x))
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

        text_loc = np.array((text_x, text_y))
        text_style['rotation'] = ax.transData.transform_angles(
            np.array((rotation,)), text_loc.reshape((1, 2)))[0]
        text_style['rotation_mode'] = 'anchor'

        if ha is not None:
            text_style['ha'] = ha
        if va is not None:
            text_style['va'] = va

        ax.annotate(label, (text_x, text_y), **text_style)

        return ax


class PsychroCurves:
    """Object to store a list of psychrometric curves for plotting."""

    def __init__(self,
                 curves: Iterable(PsychroCurve),
                 extra: dict=None,
                 family_label: str=None):
        self.curves = curves
        self.family_label = family_label
        self.extra = extra

    def __len__(self):
        """Return the # of curves."""
        return len(self.curves)

    def __iter__(self):
        """Iterate over the curves."""
        return self.curves.__iter__()

    def __repr__(self):
        """Object string representation."""
        return '<{} PsychroCurves (label: {})>'.format(
            len(self), self.family_label)

    def plot(self, ax: Axes=None):
        """Plot the family curves."""
        [curve.plot(ax) for curve in self.curves]
        # TODO family labelling here


class PsychroChart:
    """Psychrometric chart object handler"""

    def __init__(self,
                 styles: Union[dict, str]=None,
                 zones_file: Union[dict, str]=None):
        """Initialization of the PsychroChart object."""
        self.figure_params = {}
        self.dbt_min = self.dbt_max = -100
        self.w_min = self.w_max = -1
        self.altitude_m = -1
        self.chart_params = {}
        self.p_atm_kpa = -1
        self.constant_dry_temp_data = None
        self.constant_humidity_data = None
        self.constant_rh_data = None
        self.constant_h_data = None
        self.constant_v_data = None
        self.constant_wbt_data = None
        self.saturation = None

        self._make_chart_data(styles, zones_file)

    def __repr__(self) -> str:
        """String representation of the PsychroChart object."""
        return '<PsychroChart [{:g}->{:g} °C, {:g}->{:g} gr/kg_da]>'.format(
            self.dbt_min, self.dbt_max, self.w_min, self.w_max)

    @timeit('Psychrometric data generation')
    def _make_chart_data(self,
                         styles: Union[dict, str]=None,
                         zones_file: Union[dict, str]=None):
        """Generate the data to plot the psychrometric chart."""
        # Get styling
        config = load_config(styles)
        increment = config['limits']['step_temp']

        self.figure_params = config['figure']
        self.dbt_min, self.dbt_max = config['limits']['range_temp_c']
        self.w_min, self.w_max = config['limits']['range_humidity_g_kg']
        self.altitude_m = config['limits']['altitude_m']
        self.chart_params = config['chart_params']
        # Base pressure
        self.p_atm_kpa = pressure_by_altitude(self.altitude_m)

        # Dry bulb constant lines (vertical):
        if self.chart_params["with_constant_dry_temp"]:
            step = self.chart_params["constant_temp_step"]
            style = config['constant_dry_temp']
            temps_vl = np.arange(self.dbt_min, self.dbt_max, step)
            heights = [1000 * humidity_ratio(
                saturation_pressure_water_vapor(t),
                p_atm_kpa=self.p_atm_kpa) for t in temps_vl]

            self.constant_dry_temp_data = PsychroCurves(
                [PsychroCurve(np.array([t, t]),
                              np.array([self.w_min, h]), style,
                              type_curve='constant_dry_temp_data',
                              label=None)
                 for t, h in zip(temps_vl, heights)],
                family_label='Dry bulb temperature')

        # Absolute humidity constant lines (horizontal):
        if self.chart_params["with_constant_humidity"]:
            step = self.chart_params["constant_humid_step"]
            style = config['constant_humidity']
            ws_hl = np.arange(self.w_min + step, self.w_max + step / 10, step)
            dew_points = [
                iter_solver(
                    dew_point_temperature(
                        water_vapor_pressure(
                            w / 1000, p_atm_kpa=self.p_atm_kpa)),
                    w / 1000.,
                    lambda x: humidity_ratio(
                        saturation_pressure_water_vapor(x),
                        p_atm_kpa=self.p_atm_kpa),
                    initial_increment=0.25, num_iters_max=100,
                    precision=0.00001)
                for w in ws_hl]

            self.constant_humidity_data = PsychroCurves(
                [PsychroCurve(np.array([t_dp, self.dbt_max]),
                              np.array([w, w]), style,
                              type_curve='constant_humidity_data',
                              label=None)
                 for w, t_dp in zip(ws_hl, dew_points)],
                family_label='Absolute humidity')

        # Constant relative humidity curves:
        if self.chart_params["with_constant_rh"]:
            rh_perc_values = self.chart_params["constant_rh_curves"]
            rh_label_values = self.chart_params.get("constant_rh_labels", [])
            style = config["constant_rh"]
            temps_ct_rh, curves_ct_rh = _gen_mat_curves_range_temps(
                _curve_constant_humidity_ratio,
                self.dbt_min, self.dbt_max, increment,
                rh_perc_values, p_atm_kpa=self.p_atm_kpa)

            self.constant_rh_data = PsychroCurves(
                [PsychroCurve(
                    temps_ct_rh, curves_ct_rh[:, i], style,
                    type_curve='constant_rh_data',
                    label_loc=.85, label='RH {:g} %'.format(rh)
                    if round(rh, 1) in rh_label_values else None)
                    for i, rh in enumerate(rh_perc_values)],
                family_label='Constant relative humidity')

        # Constant enthalpy lines:
        if self.chart_params["with_constant_h"]:
            step = self.chart_params["constant_h_step"]
            enthalpy_values = np.arange(*self.chart_params["range_h"], step)
            h_label_values = self.chart_params.get("constant_h_labels", [])
            style = config["constant_h"]
            temps_max_constant_h = [
                dry_temperature_for_enthalpy_of_moist_air(
                    self.w_min / 1000, h)
                for h in enthalpy_values]
            sat_points = [
                iter_solver(
                    dry_temperature_for_enthalpy_of_moist_air(
                        self.w_min / 1000 + 0.1, h),
                    h,
                    lambda x: enthalpy_moist_air(
                        x, saturation_pressure_water_vapor(x),
                        p_atm_kpa=self.p_atm_kpa),
                    initial_increment=15, num_iters_max=100,
                    precision=0.0005)
                for h in enthalpy_values]

            self.constant_h_data = PsychroCurves(
                [PsychroCurve(
                    [t_sat, t_max], [1000 * humidity_ratio(
                        saturation_pressure_water_vapor(t_sat),
                        self.p_atm_kpa), self.w_min], style,
                    type_curve='constant_h_data',
                    label_loc=1., label='{:g} kJ/kg_da'.format(h)
                    if round(h, 3) in h_label_values else None)
                    for t_sat, t_max, h in zip(
                    sat_points, temps_max_constant_h, enthalpy_values)],
                family_label='Constant enthalpy')

        # Constant specific volume lines:
        if self.chart_params["with_constant_v"]:
            step = self.chart_params["constant_v_step"]
            vol_values = np.arange(
                *self.chart_params["range_vol_m3_kg"], step)
            vol_label_values = self.chart_params.get("constant_v_labels", [])
            style = config["constant_v"]
            temps_max_constant_v = [
                dry_temperature_for_specific_volume_of_moist_air(
                    0, specific_vol, p_atm_kpa=self.p_atm_kpa)
                for specific_vol in vol_values]
            sat_points = [
                iter_solver(
                    t_max - 5,
                    specific_vol,
                    lambda x: specific_volume(
                        x, saturation_pressure_water_vapor(x),
                        p_atm_kpa=self.p_atm_kpa),
                    initial_increment=2, num_iters_max=100,
                    precision=0.00005)
                for t_max, specific_vol in
                zip(temps_max_constant_v, vol_values)]

            self.constant_v_data = PsychroCurves(
                [PsychroCurve(
                    [t_sat, t_max], [1000 * humidity_ratio(
                        saturation_pressure_water_vapor(t_sat),
                        self.p_atm_kpa), 0],
                    style, type_curve='constant_v_data',
                    label_loc=1., label='{:g} m3/kg_da'.format(vol)
                    if round(vol, 3) in vol_label_values else None)
                    for t_sat, t_max, vol in zip(
                    sat_points, temps_max_constant_v, vol_values)],
                family_label='Constant specific volume')

        # Constant wet bulb temperature lines:
        if self.chart_params["with_constant_wet_temp"]:
            step = self.chart_params["constant_wet_temp_step"]
            wbt_values = np.arange(*self.chart_params["range_wet_temp"], step)
            wbt_label_values = self.chart_params.get(
                "constant_wet_temp_labels", [])
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
                    label_loc=0.05, label='{:g} °C'.format(wbt)
                    if wbt in wbt_label_values else None)
                    for wbt, w_max in zip(wbt_values, w_max_constant_wbt)],
                family_label='Constant wet bulb temperature')

        # Saturation line:
        if True:
            sat_style = config["saturation"]
            temps_sat_line, w_sat_line = _gen_mat_curves_range_temps(
                _curve_constant_humidity_ratio,
                self.dbt_min, self.dbt_max, increment,
                [100], p_atm_kpa=self.p_atm_kpa)

            self.saturation = PsychroCurve(
                temps_sat_line, w_sat_line[:, 0], sat_style,
                type_curve='saturation')

        # Zones
        if self.chart_params["with_zones"] and zones_file is None:
            # load default 'Comfort' zones (Spain RITE)
            conf_zones = load_zones()
        elif zones_file is not None:
            conf_zones = load_zones(zones_file)
        else:
            conf_zones = []

        self.zones = PsychroCurves(
            [_make_zone(zone_conf, increment, self.p_atm_kpa)
             for zone_conf in conf_zones])

    def plot(self) -> plt.Axes:
        """Plot the psychrochart and return the matplotlib Axes instance."""
        # Prepare fig & axis
        fig_params = self.figure_params.copy()
        figsize = fig_params.pop('figsize', (16, 9))
        fontsize = fig_params.pop('fontsize', 10)
        x_style = fig_params.pop('x_axis', {})
        x_style_labels = fig_params.pop('x_axis_labels', {})
        y_style = fig_params.pop('y_axis', {})
        y_style_labels = fig_params.pop('y_axis_labels', {})
        partial_axis = fig_params.pop('partial_axis', True)

        # Create figure and format axis
        fig = plt.figure(figsize=figsize)
        fig.set_tight_layout(True)
        ax = fig.gca()
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")
        plt.xlim([self.dbt_min, self.dbt_max])
        plt.ylim([self.w_min, self.w_max])

        # Apply axis styles
        if fig_params['x_label'] is not None:
            style_axis = x_style_labels.copy()
            style_axis['fontsize'] *= 1.2
            plt.xlabel(fig_params['x_label'], **style_axis)
        if fig_params['y_label'] is not None:
            style_axis = y_style_labels.copy()
            style_axis['fontsize'] *= 1.2
            plt.ylabel(fig_params['y_label'], **style_axis)
        if fig_params['title'] is not None:
            plt.title(fig_params['title'],
                      fontsize=fontsize * 1.5, fontweight='bold')

        plt.setp(ax.spines['right'], **y_style)
        plt.setp(ax.spines['bottom'], **x_style)
        if partial_axis:  # Hide left and top axis
            ax.spines['left'].set_visible(False)
            ax.spines['top'].set_visible(False)
        else:
            plt.setp(ax.spines['left'], **y_style)
            plt.setp(ax.spines['top'], **x_style)

        if self.chart_params.get("with_constant_dry_temp", True):
            step_label = self.chart_params.get(
                "constant_temp_label_step", None)
            if step_label:  # Explicit xticks
                ticks = np.arange(self.dbt_min,
                                  self.dbt_max + step_label / 10, step_label)
                ax.set_xticks(ticks)
                ax.set_xticklabels(
                    ['{:g}'.format(t) for t in ticks], **x_style_labels)
        else:
            ax.set_xticks([])

        if self.chart_params.get("with_constant_humidity", True):
            step_label = self.chart_params.get(
                "constant_humid_label_step", None)
            if step_label:  # Explicit xticks
                ticks = np.arange(self.w_min, self.w_max + step_label / 10,
                                  step_label)
                ax.set_yticks(ticks)
                ax.set_yticklabels(
                    ['{:g}'.format(t) for t in ticks], **y_style_labels)
        else:
            ax.set_yticks([])

        # Plot curves:
        [getattr(self, curve_family).plot(ax=ax)
         for curve_family in PSYCHRO_CURVES_KEYS
         if getattr(self, curve_family) is not None]

        # Plot zones:
        if self.zones:
            for zone in self.zones:
                zone.plot(ax=ax)

        return ax


def _gen_mat_curves_range_temps(
        func_curve: Callable,
        dbt_min: float, dbt_max: float, increment: float,
        curves_values: list,
        p_atm_kpa: float=PRESSURE_STD_ATM_KPA) -> tuple:
    """Generic curve generation in a range of temperatures."""
    temps = np.arange(dbt_min, dbt_max + increment, increment)
    curves = np.zeros((len(temps), len(curves_values)))

    for i, value in enumerate(curves_values):
        curves[:, i] = func_curve(
            temps, value, p_atm_kpa)
    return temps, curves


def _curve_constant_humidity_ratio(
        dry_temps: Iterable, rh_percentage: float=100.,
        p_atm_kpa: float=PRESSURE_STD_ATM_KPA, mode_sat=1) -> np.array:
    """Generate a curve (numpy array) of constant humidity ratio."""
    return np.array(
        [1000 * humidity_ratio(
            saturation_pressure_water_vapor(t, mode=mode_sat)
            * rh_percentage / 100., p_atm_kpa)
         for t in dry_temps])


def _make_zone_dbt_rh(
        t_min: float, t_max: float, increment: float,
        rh_min: float, rh_max: float,
        p_atm_kpa: float=PRESSURE_STD_ATM_KPA,
        style: dict=None, label: str=None) -> PsychroCurve:
    """Generate points for zone between constant dry bulb temps and RH."""
    temps = np.arange(t_min, t_max + increment, increment)
    curve_rh_up = _curve_constant_humidity_ratio(temps, rh_max, p_atm_kpa)
    curve_rh_down = _curve_constant_humidity_ratio(temps, rh_min, p_atm_kpa)
    abs_humid = np.array(list(curve_rh_up)
                         + list(curve_rh_down[::-1]) + [curve_rh_up[0]])
    temps_zone = np.array(list(temps) + list(temps[::-1]) + [temps[0]])
    return PsychroCurve(temps_zone, abs_humid, style,
                        type_curve='constant_rh_data', label=label)


def _make_zone(
        zone_conf: dict, increment: float,
        p_atm_kpa: float=PRESSURE_STD_ATM_KPA) -> PsychroCurve:
    """Generate points for zone between constant dry bulb temps and RH."""
    if zone_conf['zone_type'] == 'dbt-rh':
        return _make_zone_dbt_rh(
            *zone_conf['points_x'], increment,
            *zone_conf['points_y'], p_atm_kpa, zone_conf['style'])
