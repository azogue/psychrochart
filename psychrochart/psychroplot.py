# -*- coding: utf-8 -*-
"""
A python library to make psychrometric charts and overlay information in them.

"""
import matplotlib.pyplot as plt
import numpy as np

from psychrochart.psychrovars import (
    PRESSURE_STD_ATM_KPA, press_and_temp_by_altitude, humidity_ratio,
    specific_volume, dew_point_temperature, water_vapor_pressure,
    enthalpy_moist_air, saturation_pressure_water_vapor,
    dry_temperature_for_enthalpy_of_moist_air, relative_humidity_from_temps,
    dry_temperature_for_specific_volume_of_moist_air
)
from psychrochart.util import load_config, iter_solver


# CURVE GENERATION
def _gen_mat_curves_range_temps(
        func_curve, dbt_min, dbt_max, increment,
        curves_values,
        p_atm_kpa=PRESSURE_STD_ATM_KPA):
    temps = np.arange(dbt_min, dbt_max + increment, increment)
    curves = np.zeros((len(temps), len(curves_values)))

    for i, value in enumerate(curves_values):
        curves[:, i] = func_curve(
            temps, value, p_atm_kpa)
    return temps, curves


def _curve_constant_humidity_ratio(
        dry_temps, rh_percentage=100.,
        p_atm_kpa=PRESSURE_STD_ATM_KPA, mode_sat=1):
    return np.array(
        [1000 * humidity_ratio(
            saturation_pressure_water_vapor(t, mode=mode_sat)
            * rh_percentage / 100., p_atm_kpa)
         for t in dry_temps])


def i_get_figure(figsize=(16, 9), x_label=None, y_label=None, title=None):
    fig = plt.figure(figsize=figsize)
    fig.gca().yaxis.tick_right()
    if x_label is not None:
        plt.xlabel(x_label, fontsize=11)
    if y_label is not None:
        plt.ylabel(y_label, fontsize=11)
        fig.gca().yaxis.set_label_position("right")
    if title is not None:
        plt.title(title, fontsize=14, fontweight='bold')
    return fig


def _plot_zone(t_min, t_max, increment, rh_min, rh_max,
               p_atm_kpa=PRESSURE_STD_ATM_KPA,
               color='m', line_width=3):
    # Dibuja sector entre T1-T2 y HR1-HR2
    temps = np.arange(t_min, t_max + increment, increment)

    curve_rh_up = _curve_constant_humidity_ratio(temps, rh_max, p_atm_kpa)
    curve_rh_down = _curve_constant_humidity_ratio(temps, rh_min, p_atm_kpa)
    abs_humid = np.array(list(curve_rh_up)
                         + list(curve_rh_down[::-1]) + [curve_rh_up[0]])
    temps_zone = np.array(list(temps) + list(temps[::-1]) + [temps[0]])
    plt.plot(temps_zone, abs_humid, color=color, lw=line_width)


def plot_psychrochart(styles=None):
    """Plot the psychrometric chart.

    Return the matplotlib figure."""

    # Get styling
    config = load_config(styles)
    dbt_min, dbt_max = config['limits']['range_temp_c']
    w_min, w_max = config['limits']['range_humidity_g_kg']
    altitude_m = config['limits']['altitude_m']
    increment = config['limits']['step_temp']
    chart_params = config['chart_params']

    # Base pressure
    p_atm_kpa, _temp_ref = press_and_temp_by_altitude(altitude_m)

    # Prepare fig & axis
    fig = i_get_figure(**config['figure'])
    plt.xlim([dbt_min, dbt_max])
    plt.ylim([w_min, w_max])

    # Dry bulb constant lines (vertical):
    if chart_params["with_constant_dry_temp"]:
        step = chart_params["constant_temp_step"]
        style = config['constant_dry_temp']
        temps_vl = np.arange(dbt_min, dbt_max, step)
        heights = [1000 * humidity_ratio(
            saturation_pressure_water_vapor(t),
            p_atm_kpa=p_atm_kpa) for t in temps_vl]
        plt.vlines(
            temps_vl, [w_min], heights, color=style['color'],
            linewidth=style['linewidth'], linestyle=style['linestyle'])

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
        plt.hlines(
            ws_hl, dew_points, dbt_max, color=style['color'],
            linewidth=style['linewidth'], linestyle=style['linestyle'])

    # Constant relative humidity curves:
    if chart_params["with_constant_rh"]:
        rh_perc_values = chart_params["constant_rh_curves"]
        style = config["constant_rh"]
        temps_constant_rh, curves_constant_rh = _gen_mat_curves_range_temps(
            _curve_constant_humidity_ratio,
            dbt_min, dbt_max, increment,
            rh_perc_values, p_atm_kpa=p_atm_kpa)
        for i, rh_value in enumerate(rh_perc_values):
            plt.plot(temps_constant_rh, curves_constant_rh[:, i], **style)

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
        [plt.plot([t_sat, t_max],
                  [1000 * humidity_ratio(
                      saturation_pressure_water_vapor(t_sat), p_atm_kpa),
                   w_min],
                  **style)
         for t_sat, t_max in zip(sat_points, temps_max_constant_h)]

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
        [plt.plot([t_sat, t_max],
                  [1000 * humidity_ratio(
                      saturation_pressure_water_vapor(t_sat), p_atm_kpa),
                   0],
                  **style)
         for t_sat, t_max in zip(sat_points, temps_max_constant_v)]

    # Constant wet bulb temperature lines:
    if chart_params["with_constant_wet_temp"]:
        step = chart_params["constant_wet_temp_step"]
        wbt_values = np.arange(*chart_params["range_wet_temp"], step)
        style = config["constant_wet_temp"]
        w_max_constant_wbt = [
            humidity_ratio(saturation_pressure_water_vapor(wbt), p_atm_kpa)
            for wbt in wbt_values]
        for wbt, w_max in zip(wbt_values, w_max_constant_wbt):
            w_2 = humidity_ratio(
                saturation_pressure_water_vapor(dbt_max)
                * relative_humidity_from_temps(
                    dbt_max, wbt, p_atm_kpa=p_atm_kpa),
                p_atm_kpa=p_atm_kpa)
            plt.plot([wbt, dbt_max], [1000 * w_max, 1000 * w_2], **style)

    # Saturation line:
    if True:
        sat_style = config["saturation"]
        temps_sat_line, w_sat_line = _gen_mat_curves_range_temps(
            _curve_constant_humidity_ratio,
            dbt_min, dbt_max, increment,
            [100], p_atm_kpa=p_atm_kpa)
        plt.plot(temps_sat_line, w_sat_line[:, 0], **sat_style)

    # Comfort zones (Spain RITE)
    _plot_zone(23, 25, increment, 45, 60, p_atm_kpa, 'r', 3)
    _plot_zone(21, 23, increment, 40, 50, p_atm_kpa, 'c', 2)

    return fig
