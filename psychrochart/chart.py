# -*- coding: utf-8 -*-
"""
A python library to make psychrometric charts and overlay information in them.

"""
from collections import namedtuple
import json
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import numpy as np
from typing import Iterable

from psychrochart.equations import (
    PRESSURE_STD_ATM_KPA, pressure_by_altitude, humidity_ratio,
    specific_volume, dew_point_temperature, water_vapor_pressure,
    enthalpy_moist_air, saturation_pressure_water_vapor,
    dry_temperature_for_enthalpy_of_moist_air, relative_humidity_from_temps,
    dry_temperature_for_specific_volume_of_moist_air
)
from psychrochart.util import load_config, iter_solver, timeit


PSYCHRO_CURVES_KEYS = [
    'constant_dry_temp_data', 'constant_humidity_data',
    'constant_h_data', 'constant_v_data', 'constant_rh_data',
    'constant_wbt_data', 'saturation']


class PsychroCurve:
    """Object to store a psychrometric curve for plotting."""

    def __init__(self,
                 x_data: np.array=None,
                 y_data: np.array=None,
                 style: dict=None,
                 label_value: float=None):
        self.x_data = x_data
        self.y_data = y_data
        self.style = style
        self.label_value = label_value

    def __dict__(self) -> dict:
        """Return the curve as a dict."""
        return {
            "x_data": self.x_data,
            "y_data": self.y_data,
            "style": self.style,
            "label_value": self.label_value}

    def __bool__(self):
        """Return the valid existence of the curve."""
        if self.x_data is not None and len(self.x_data) > 1 \
                and self.y_data is not None and len(self.y_data) > 1:
            return True
        return False

    def __repr__(self):
        """Object string representation."""
        if self:
            return '<PsychroCurve {} values (label: {})>'.format(
                len(self.x_data), self.label_value)
        else:
            return '<Empty PsychroCurve (label: {})>'.format(self.label_value)

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
        self.label_value = data.get('label_value')
        return self

    def plot(self, ax: Axes=None):
        """Plot the curve."""
        if ax is not None:
            ax.plot(self.x_data, self.y_data, **dict(self.style))
        else:
            plt.plot(self.x_data, self.y_data, **dict(self.style))
        # TODO curve labelling here


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
        yield next(self.curves.__iter__())

    def __repr__(self):
        """Object string representation."""
        return '<{} PsychroCurves (label: {})>'.format(
            len(self), self.family_label)

    def plot(self, ax: Axes=None):
        """Plot the family curves."""
        [curve.plot(ax) for curve in self.curves]
        # TODO family labelling here


# TODO convertir a clase heredada
PsychroData = namedtuple(
        'PsychroData',
        ['limits', 'p_atm_kpa', 'dbt_min', 'dbt_max', 'w_min', 'w_max',
         'figure', 'chart_params',
         'constant_dry_temp_data', 'constant_humidity_data',
         'constant_rh_data', 'constant_h_data', 'constant_v_data',
         'constant_wbt_data', 'saturation', 'zones'])


def _gen_mat_curves_range_temps(
        func_curve, dbt_min, dbt_max, increment,
        curves_values,
        p_atm_kpa=PRESSURE_STD_ATM_KPA):
    """Generic curve generation in a range of temperatures."""
    temps = np.arange(dbt_min, dbt_max + increment, increment)
    curves = np.zeros((len(temps), len(curves_values)))

    for i, value in enumerate(curves_values):
        curves[:, i] = func_curve(
            temps, value, p_atm_kpa)
    return temps, curves


def _curve_constant_humidity_ratio(
        dry_temps, rh_percentage=100.,
        p_atm_kpa=PRESSURE_STD_ATM_KPA, mode_sat=1):
    """Generate a curve (numpy array) of constant humidity ratio."""
    return np.array(
        [1000 * humidity_ratio(
            saturation_pressure_water_vapor(t, mode=mode_sat)
            * rh_percentage / 100., p_atm_kpa)
         for t in dry_temps])


def _make_zone_dbt_rh(
        t_min, t_max, increment, rh_min, rh_max,
        p_atm_kpa=PRESSURE_STD_ATM_KPA,
        style=None):
    """Generate points for zone between constant dry bulb temps and RH."""
    temps = np.arange(t_min, t_max + increment, increment)
    curve_rh_up = _curve_constant_humidity_ratio(temps, rh_max, p_atm_kpa)
    curve_rh_down = _curve_constant_humidity_ratio(temps, rh_min, p_atm_kpa)
    abs_humid = np.array(list(curve_rh_up)
                         + list(curve_rh_down[::-1]) + [curve_rh_up[0]])
    temps_zone = np.array(list(temps) + list(temps[::-1]) + [temps[0]])
    return PsychroCurve(temps_zone, abs_humid, style,
                        label_value=(t_max + t_min) / 2)


@timeit('Psychrometric data generation')
def data_psychrochart(styles=None) -> PsychroData:
    """Generate the data to plot the psychrometric chart.

    # Return a namedtuple object (PsychroData)."""
    # Get styling
    config = load_config(styles)
    dbt_min, dbt_max = config['limits']['range_temp_c']
    w_min, w_max = config['limits']['range_humidity_g_kg']
    altitude_m = config['limits']['altitude_m']
    increment = config['limits']['step_temp']
    chart_params = config['chart_params']

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
                          np.array([w_min, h]), style, label_value=t)
             for t, h in zip(temps_vl, heights)],
            family_label='Dry bulb temperature')

    # Absolute humidity constant lines (horizontal):
    if chart_params["with_constant_humidity"]:
        step = chart_params["constant_humid_step"]
        style = config['constant_humidity']
        ws_hl = np.arange(max(step, w_min), w_max, step)
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
                          np.array([w, w]), style, label_value=w)
             for w, t_dp in zip(ws_hl, dew_points)],
            family_label='Absolute humidity')

    # Constant relative humidity curves:
    if chart_params["with_constant_rh"]:
        rh_perc_values = chart_params["constant_rh_curves"]
        style = config["constant_rh"]
        temps_constant_rh, curves_constant_rh = _gen_mat_curves_range_temps(
            _curve_constant_humidity_ratio,
            dbt_min, dbt_max, increment,
            rh_perc_values, p_atm_kpa=p_atm_kpa)

        constant_rh_data = PsychroCurves(
            [PsychroCurve(temps_constant_rh, curves_constant_rh[:, i],
                          style, label_value=rh)
             for i, rh in enumerate(rh_perc_values)],
            family_label='Constant relative humidity')

    # Constant enthalpy lines:
    if chart_params["with_constant_h"]:
        step = chart_params["constant_h_step"]
        enthalpy_values = np.arange(*chart_params["range_h"], step)
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
            [PsychroCurve([t_sat, t_max],
                          [1000 * humidity_ratio(
                              saturation_pressure_water_vapor(t_sat),
                              p_atm_kpa), w_min], style, label_value=h)
             for t_sat, t_max, h in zip(
                sat_points, temps_max_constant_h, enthalpy_values)],
            family_label='Constant enthalpy')

    # Constant specific volume lines:
    if chart_params["with_constant_v"]:
        step = chart_params["constant_v_step"]
        vol_values = np.arange(*chart_params["range_vol_m3_kg"], step)
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
            [PsychroCurve([t_sat, t_max],
                          [1000 * humidity_ratio(
                              saturation_pressure_water_vapor(t_sat),
                              p_atm_kpa), 0], style, label_value=vol)
             for t_sat, t_max, vol in zip(
                sat_points, temps_max_constant_v, vol_values)],
            family_label='Constant specific volume')

    # Constant wet bulb temperature lines:
    if chart_params["with_constant_wet_temp"]:
        step = chart_params["constant_wet_temp_step"]
        wbt_values = np.arange(*chart_params["range_wet_temp"], step)
        style = config["constant_wet_temp"]
        w_max_constant_wbt = [humidity_ratio(
            saturation_pressure_water_vapor(wbt), p_atm_kpa)
            for wbt in wbt_values]

        constant_wbt_data = PsychroCurves(
            [PsychroCurve([wbt, dbt_max],
                          [1000 * w_max,
                           1000 * humidity_ratio(
                               saturation_pressure_water_vapor(dbt_max)
                               * relative_humidity_from_temps(
                                   dbt_max, wbt, p_atm_kpa=p_atm_kpa),
                               p_atm_kpa=p_atm_kpa)],
                          style, label_value=wbt)
             for wbt, w_max in zip(wbt_values, w_max_constant_wbt)],
            family_label='Constant wet bulb temperature')

    # Saturation line:
    if True:
        sat_style = config["saturation"]
        temps_sat_line, w_sat_line = _gen_mat_curves_range_temps(
            _curve_constant_humidity_ratio,
            dbt_min, dbt_max, increment,
            [100], p_atm_kpa=p_atm_kpa)

        saturation = PsychroCurve(temps_sat_line, w_sat_line[:, 0],
                                  sat_style, label_value=100.)

    # TODO añadir zonas desde config
    # Comfort zones (Spain RITE)
    style_z1 = {"color": "r", "linewidth": 3, "linestyle": ":"}
    style_z2 = {"color": "c", "linewidth": 2, "linestyle": ":"}
    zones = PsychroCurves(
        [_make_zone_dbt_rh(23, 25, increment, 45, 60, p_atm_kpa, style_z1),
         _make_zone_dbt_rh(21, 23, increment, 40, 50, p_atm_kpa, style_z2)])

    data = PsychroData(
        config['limits'], p_atm_kpa, dbt_min, dbt_max, w_min, w_max,
        config['figure'], chart_params,
        constant_dry_temp_data, constant_humidity_data,
        constant_rh_data, constant_h_data, constant_v_data,
        constant_wbt_data, saturation, zones)

    return data
