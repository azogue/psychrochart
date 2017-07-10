# -*- coding: utf-8 -*-
"""
A python library to make psychrometric charts and overlay information in them.

"""
from collections import namedtuple
import json
from math import atan2, degrees
from matplotlib.axes import Axes
import matplotlib.patches as patches
from matplotlib.path import Path
import matplotlib.pyplot as plt
import numpy as np
from typing import Iterable, Callable

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
PSYCHRO_DATA_KEYS = [
    'p_atm_kpa', 'dbt_min', 'dbt_max', 'w_min', 'w_max',
    'figure', 'chart_params'] + PSYCHRO_CURVES_KEYS + ['zones']


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

    def plot(self, ax: Axes=None, limits: tuple=None):
        """Plot the curve."""
        if ax is None:
            ax = plt.gca()

        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        if not _between_limits(self.x_data, self.y_data,
                               xmin, xmax, ymin, ymax):
            print('{} Not between limits ([{}, {}, {}, {}]) -> x:{}, y:{}'
                  .format(self._type_curve, xmin, xmax, ymin, ymax, self.x_data, self.y_data))
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

        # def add_label(self, ax: Axes = None):
        #     """Plot the curve."""

        # TODO curve labelling here
        if not self._is_patch and self._label is not None:
            num_samples = len(self.x_data)
            assert len(self.y_data) > 1

            fig_size = ax.get_figure().get_size_inches()
            ax_size = ax.get_position().size
            fig_ratio = fig_size[0] * ax_size[0] / (fig_size[1] * ax_size[1])

            if num_samples == 2:
                delta_x = self.x_data[1] - self.x_data[0]
                delta_y = self.y_data[1] - self.y_data[0]
                if delta_x == 0:
                    rotation = 90  # up to bottom
                    xy = (self.x_data[0],
                          (self.y_data[0] + self._label_loc * delta_y))
                    text_style = {'rotation': rotation,
                                  'va': 'baseline', 'ha': 'left'}
                elif self._label_loc == 1.:
                    if self.x_data[1] > xmax:
                        tilt = delta_y / delta_x
                        xy = (xmax,
                              self.y_data[0] + tilt * (xmax - self.x_data[0]))
                    else:
                        xy = (self.x_data[1], self.y_data[1])
                    rotation = degrees(atan2(delta_y / fig_ratio, delta_x))
                    # print('XY -> ', self._type_curve, xy, rotation)
                    text_style = {'rotation': rotation,
                                  "rotation_mode": "anchor",
                                  'va': 'bottom', 'ha': 'right'}
                else:
                    tilt = delta_y / delta_x
                    x = self.x_data[0] + self._label_loc * (xmax - xmin)
                    if x < xmin:
                        # print('enderezando: ', self._type_curve)
                        x = xmin + self._label_loc * (xmax - xmin)
                    y = self.y_data[0] + tilt * (x - self.x_data[0])
                    xy = (x, y)
                    rotation = degrees(atan2(delta_y / fig_ratio, delta_x))
                    # print('XY left-> ', self._type_curve, xy, rotation)
                    text_style = {'rotation': rotation,
                                  "rotation_mode": "anchor",
                                  'va': 'bottom', 'ha': 'left'}
            else:
                idx = int(num_samples * self._label_loc)
                if idx == num_samples - 1:
                    idx -= 1
                delta_x = self.x_data[idx + 1] - self.x_data[idx]
                delta_y = self.y_data[idx + 1] - self.y_data[idx]

                rotation = degrees(atan2(delta_y / fig_ratio, delta_x * fig_ratio))
                xy = (self.x_data[idx], self.y_data[idx])
                text_style = {'rotation': rotation,
                              "rotation_mode": "anchor",
                              'va': 'bottom', 'ha': 'center'}
            if 'color' in self.style:
                text_style['color'] = mod_color(self.style['color'], -25)
            ax.annotate(self._label, xy, **text_style)


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

    def plot(self, ax: Axes=None, limits: tuple=None):
        """Plot the family curves."""
        [curve.plot(ax, limits=limits) for curve in self.curves]
        # TODO family labelling here


class PsychroChart:
    """Psychrometric chart object handler"""

    def __init__(self, *data_args):
        """Initialization of the PsychroChart object."""
        named_tuple = namedtuple('PsychroChart', PSYCHRO_DATA_KEYS)
        self._data = named_tuple(*data_args)
        # noinspection PyProtectedMember
        [self.__setattr__(name, value)
         for name, value in zip(self._data._fields, self._data)]

    def __repr__(self) -> str:
        """String representation of the PsychroChart object."""
        # noinspection PyProtectedMember
        return '<PsychroChart object, data: {}>'.format(self._data._fields)

    def __getitem__(self, item: str) -> PsychroCurves:
        """Getitem with data keys."""
        return getattr(self._data, item, None)

    def plot(self) -> plt.Axes:
        """Plot the psychrochart and return the matplotlib Axes instance."""
        # Prepare fig & axis
        fig_params = self._data.figure.copy()
        figsize = fig_params.pop('figsize', (16, 9))
        fontsize = fig_params.pop('fontsize', 10)
        x_style = fig_params.pop('x_axis', {})
        x_style_labels = fig_params.pop('x_axis_labels', {})
        y_style = fig_params.pop('y_axis', {})
        y_style_labels = fig_params.pop('y_axis_labels', {})
        partial_axis = fig_params.pop('partial_axis', True)
        chart_params = self._data.chart_params
        limits = (self._data.dbt_min, self._data.dbt_max,
                  self._data.w_min, self._data.w_max)

        # Create figure and format axis
        fig = plt.figure(figsize=figsize)
        fig.set_tight_layout(True)
        ax = fig.gca()
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")
        plt.xlim([limits[0], limits[1]])
        plt.ylim([limits[2], limits[3]])

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

        if chart_params.get("with_constant_dry_temp", True):
            step_label = chart_params.get("constant_temp_label_step", None)
            if step_label:  # Explicit xticks
                ticks = np.arange(limits[0], limits[1] + step_label / 10,
                                  step_label)
                ax.set_xticks(ticks)
                ax.set_xticklabels(
                    ['{:g}'.format(t) for t in ticks], **x_style_labels)

        if chart_params.get("with_constant_humidity", True):
            step_label = chart_params.get("constant_humid_label_step", None)
            if step_label:  # Explicit xticks
                ticks = np.arange(limits[2], limits[3] + step_label / 10,
                                  step_label)
                ax.set_yticks(ticks)
                ax.set_yticklabels(
                    ['{:g}'.format(t) for t in ticks], **y_style_labels)

        # Plot curves:
        [self[curve_family].plot(ax=ax, limits=limits)
         for curve_family in PSYCHRO_CURVES_KEYS
         if self[curve_family] is not None]

        # TODO añadir zonas como overlay externo
        # Comfort zones (Spain RITE)
        if self._data.zones:
            for zone in self._data.zones:
                zone.plot(ax=ax, limits=limits)

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

    # 'fill_color': [0.859, 0.0, 0.6], 'label': None,


@timeit('Psychrometric data generation')
def data_psychrochart(styles=None, zones_file=None) -> PsychroChart:
    """Generate the data to plot the psychrometric chart.

    Return a PsychroChart object."""
    # Get styling
    config = load_config(styles)
    dbt_min, dbt_max = config['limits']['range_temp_c']
    w_min, w_max = config['limits']['range_humidity_g_kg']
    altitude_m = config['limits']['altitude_m']
    increment = config['limits']['step_temp']
    chart_params = config['chart_params']
    limits = [dbt_min, dbt_max, w_min, w_max]

    # Base pressure
    p_atm_kpa = pressure_by_altitude(altitude_m)

    # Init curve families:
    constant_dry_temp_data = constant_humidity_data = constant_rh_data \
        = constant_h_data = constant_v_data \
        = constant_wbt_data = saturation = None

    # Dry bulb constant lines (vertical):
    if chart_params["with_constant_dry_temp"]:
        step = chart_params["constant_temp_step"]
        style = config['constant_dry_temp']
        temps_vl = np.arange(dbt_min, dbt_max, step)
        heights = [1000 * humidity_ratio(
            saturation_pressure_water_vapor(t),
            p_atm_kpa=p_atm_kpa) for t in temps_vl]

        constant_dry_temp_data = PsychroCurves(
            [PsychroCurve(np.array([t, t]),
                          np.array([w_min, h]), style,
                          type_curve='constant_dry_temp_data', label=None)
             for t, h in zip(temps_vl, heights)],
            family_label='Dry bulb temperature')

    # Absolute humidity constant lines (horizontal):
    if chart_params["with_constant_humidity"]:
        step = chart_params["constant_humid_step"]
        style = config['constant_humidity']
        ws_hl = np.arange(w_min + step, w_max + step / 10, step)
        dew_points = [
            iter_solver(
                dew_point_temperature(
                    water_vapor_pressure(w / 1000, p_atm_kpa=p_atm_kpa)),
                w / 1000.,
                lambda x: humidity_ratio(
                    saturation_pressure_water_vapor(x), p_atm_kpa=p_atm_kpa),
                initial_increment=0.25, num_iters_max=100, precision=0.00001)
            for w in ws_hl]

        constant_humidity_data = PsychroCurves(
            [PsychroCurve(np.array([t_dp, dbt_max]),
                          np.array([w, w]), style,
                          type_curve='constant_humidity_data', label=None)
             for w, t_dp in zip(ws_hl, dew_points)],
            family_label='Absolute humidity')

    # Constant relative humidity curves:
    if chart_params["with_constant_rh"]:
        rh_perc_values = chart_params["constant_rh_curves"]
        rh_label_values = chart_params.get("constant_rh_labels", [])
        style = config["constant_rh"]
        temps_constant_rh, curves_constant_rh = _gen_mat_curves_range_temps(
            _curve_constant_humidity_ratio,
            dbt_min, dbt_max, increment,
            rh_perc_values, p_atm_kpa=p_atm_kpa)

        constant_rh_data = PsychroCurves(
            [PsychroCurve(
                temps_constant_rh, curves_constant_rh[:, i], style,
                type_curve='constant_rh_data',
                label_loc=.85, label='RH {:g} %'.format(rh)
                if round(rh, 1) in rh_label_values else None)
             for i, rh in enumerate(rh_perc_values)],
            family_label='Constant relative humidity')

    # Constant enthalpy lines:
    if chart_params["with_constant_h"]:
        step = chart_params["constant_h_step"]
        enthalpy_values = np.arange(*chart_params["range_h"], step)
        h_label_values = chart_params.get("constant_h_labels", [])
        style = config["constant_h"]
        temps_max_constant_h = [
            dry_temperature_for_enthalpy_of_moist_air(w_min / 1000, h)
            for h in enthalpy_values]
        sat_points = [
            iter_solver(
                dry_temperature_for_enthalpy_of_moist_air(
                    w_min / 1000 + 0.1, h),
                h,
                lambda x: enthalpy_moist_air(
                    x, saturation_pressure_water_vapor(x),
                    p_atm_kpa=p_atm_kpa),
                initial_increment=15, num_iters_max=100, precision=0.0005)
            for h in enthalpy_values]

        constant_h_data = PsychroCurves(
            [PsychroCurve(
                [t_sat, t_max], [1000 * humidity_ratio(
                    saturation_pressure_water_vapor(t_sat), p_atm_kpa),
                                 w_min], style,
                type_curve='constant_h_data',
                label_loc=1., label='H = {:g} kJ/kg_da'.format(h)
                if round(h, 3) in h_label_values else None)
             for t_sat, t_max, h in zip(
                sat_points, temps_max_constant_h, enthalpy_values)],
            family_label='Constant enthalpy')

    # Constant specific volume lines:
    if chart_params["with_constant_v"]:
        step = chart_params["constant_v_step"]
        vol_values = np.arange(*chart_params["range_vol_m3_kg"], step)
        vol_label_values = chart_params.get("constant_v_labels", [])
        style = config["constant_v"]
        temps_max_constant_v = [
            dry_temperature_for_specific_volume_of_moist_air(
                0, specific_vol, p_atm_kpa=p_atm_kpa)
            for specific_vol in vol_values]
        sat_points = [
            iter_solver(
                t_max - 5,
                specific_vol,
                lambda x: specific_volume(
                    x, saturation_pressure_water_vapor(x),
                    p_atm_kpa=p_atm_kpa),
                initial_increment=2, num_iters_max=100, precision=0.00005)
            for t_max, specific_vol in zip(temps_max_constant_v, vol_values)]

        constant_v_data = PsychroCurves(
            [PsychroCurve(
                [t_sat, t_max], [1000 * humidity_ratio(
                    saturation_pressure_water_vapor(t_sat), p_atm_kpa), 0],
                style, type_curve='constant_v_data',
                label_loc=1., label='V = {:g} m3/kg_da'.format(vol)
                if round(vol, 3) in vol_label_values else None)
             for t_sat, t_max, vol in zip(
                sat_points, temps_max_constant_v, vol_values)],
            family_label='Constant specific volume')

    # Constant wet bulb temperature lines:
    if chart_params["with_constant_wet_temp"]:
        step = chart_params["constant_wet_temp_step"]
        wbt_values = np.arange(*chart_params["range_wet_temp"], step)
        wbt_label_values = chart_params.get("constant_wet_temp_labels", [])
        style = config["constant_wet_temp"]
        w_max_constant_wbt = [humidity_ratio(
            saturation_pressure_water_vapor(wbt), p_atm_kpa)
            for wbt in wbt_values]

        constant_wbt_data = PsychroCurves(
            [PsychroCurve(
                [wbt, dbt_max], [1000 * w_max,
                                 1000 * humidity_ratio(
                                     saturation_pressure_water_vapor(dbt_max)
                                     * relative_humidity_from_temps(
                                         dbt_max, wbt, p_atm_kpa=p_atm_kpa),
                                     p_atm_kpa=p_atm_kpa)], style,
                type_curve='constant_wbt_data',
                label_loc=0.05, label='WBT {:g} ºC'.format(wbt)
                if wbt in wbt_label_values else None)
             for wbt, w_max in zip(wbt_values, w_max_constant_wbt)],
            family_label='Constant wet bulb temperature')

    # Saturation line:
    if True:
        sat_style = config["saturation"]
        temps_sat_line, w_sat_line = _gen_mat_curves_range_temps(
            _curve_constant_humidity_ratio,
            dbt_min, dbt_max, increment,
            [100], p_atm_kpa=p_atm_kpa)

        saturation = PsychroCurve(temps_sat_line, w_sat_line[:, 0], sat_style,
                                  type_curve='saturation')

    # TODO añadir zonas desde config
    # Comfort zones (Spain RITE)
    if zones_file is None:
        conf_zones = load_zones()
    else:
        conf_zones = load_zones(zones_file)

    zones = PsychroCurves(
        [_make_zone(zone_conf, increment, p_atm_kpa)
         for zone_conf in conf_zones])

    data = PsychroChart(
        p_atm_kpa, dbt_min, dbt_max, w_min, w_max,
        config['figure'], chart_params,
        constant_dry_temp_data, constant_humidity_data,
        constant_rh_data, constant_h_data, constant_v_data,
        constant_wbt_data, saturation, zones)

    return data
