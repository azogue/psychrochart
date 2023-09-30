import logging

import numpy as np
import psychrolib as psy
from psychrolib import (
    GetStandardAtmPressure,
    GetUnitSystem,
    IP,
    SetUnitSystem,
    SI,
)
from scipy.interpolate import interp1d

from psychrochart.chartdata import (
    get_rh_max_min_in_limits,
    make_constant_dry_bulb_v_lines,
    make_constant_enthalpy_lines,
    make_constant_humidity_ratio_h_lines,
    make_constant_relative_humidity_lines,
    make_constant_specific_volume_lines,
    make_constant_wet_bulb_temperature_lines,
    make_saturation_line,
)
from psychrochart.chartzones import make_zone_curve
from psychrochart.models.config import ChartConfig, ChartLimits, DEFAULT_ZONES
from psychrochart.models.curves import PsychroChartModel

spec_vol_vec = np.vectorize(psy.GetMoistAirVolume)


def set_unit_system(use_unit_system_si: bool = True) -> None:
    """Set unit system for psychrolib."""
    if use_unit_system_si and GetUnitSystem() != SI:
        SetUnitSystem(SI)
        logging.info("[SI units mode] ENABLED")
    elif not use_unit_system_si and GetUnitSystem() != IP:
        SetUnitSystem(IP)
        logging.info("[IP units mode] ENABLED")


def get_pressure_pa(limits: ChartLimits, unit_system_si: bool = True) -> float:
    """Set unit system and process ChartLimits for base pressure for chart."""
    set_unit_system(unit_system_si)
    if limits.pressure_kpa is not None:
        return limits.pressure_kpa * 1000.0  # to Pa
    else:
        return GetStandardAtmPressure(limits.altitude_m)


def _gen_interior_lines(config: ChartConfig, chart: PsychroChartModel) -> None:
    # check chart limits are not fully above the saturation curve!
    assert (chart.saturation.y_data > config.w_min).any()
    # check if sat curve cuts x-axis with T > config.dbt_min
    dbt_min_seen: float | None = None
    if chart.saturation.y_data[0] < config.w_min:
        temp_sat_interpolator = interp1d(
            chart.saturation.y_data,
            chart.saturation.x_data,
            assume_sorted=True,
        )
        dbt_min_seen = temp_sat_interpolator(config.w_min)

    # Dry bulb constant lines (vertical):
    if config.chart_params.with_constant_dry_temp:
        step = config.chart_params.constant_temp_step
        temps_vl = np.arange(config.dbt_min, config.dbt_max, step)
        if dbt_min_seen:
            temps_vl = temps_vl[temps_vl > dbt_min_seen]
        chart.constant_dry_temp_data = make_constant_dry_bulb_v_lines(
            config.w_min,
            chart.pressure,
            temps_vl=temps_vl,
            style=config.constant_dry_temp,
            family_label=config.chart_params.constant_temp_label,
        )
    else:
        chart.constant_dry_temp_data = None

    # Absolute humidity constant lines (horizontal):
    if config.chart_params.with_constant_humidity:
        step = config.chart_params.constant_humid_step
        chart.constant_humidity_data = make_constant_humidity_ratio_h_lines(
            config.dbt_max,
            chart.pressure,
            ws_hl=np.arange(
                config.w_min + step,
                config.w_max + step / 10,
                step,
            ),
            style=config.constant_humidity,
            family_label=config.chart_params.constant_humid_label,
        )
    else:
        chart.constant_humidity_data = None

    # Constant relative humidity curves:
    if config.chart_params.with_constant_rh:
        rh_min, rh_max = get_rh_max_min_in_limits(
            dbt_min_seen or config.dbt_min,
            config.dbt_max,
            config.w_min,
            config.w_max,
            chart.pressure,
        )
        rh_values = sorted(
            rh
            for rh in config.chart_params.constant_rh_curves
            if rh_min < rh < rh_max
        )
        start = (
            config.limits.step_temp * (dbt_min_seen // config.limits.step_temp)
            if dbt_min_seen
            else config.dbt_min
        )
        chart.constant_rh_data = make_constant_relative_humidity_lines(
            start,
            config.dbt_max,
            config.limits.step_temp,
            chart.pressure,
            rh_perc_values=rh_values,
            rh_label_values=config.chart_params.constant_rh_labels,
            style=config.constant_rh,
            label_loc=config.chart_params.constant_rh_labels_loc,
            family_label=config.chart_params.constant_rh_label,
            annotation_style=config.constant_rh_annotation,
        )
    else:
        chart.constant_rh_data = None

    # Constant enthalpy lines:
    if config.chart_params.with_constant_h:
        step = config.chart_params.constant_h_step
        start, end = config.chart_params.range_h
        delta_t = config.limits.range_temp_c[1] - config.limits.range_temp_c[0]
        chart.constant_h_data = make_constant_enthalpy_lines(
            config.w_min,
            chart.pressure,
            enthalpy_values=np.arange(start, end, step),
            delta_t=delta_t,
            h_label_values=config.chart_params.constant_h_labels,
            style=config.constant_h,
            label_loc=config.chart_params.constant_h_labels_loc,
            family_label=config.chart_params.constant_h_label,
            saturation_curve=chart.saturation,
            dbt_min_seen=dbt_min_seen,
            annotation_style=config.constant_h_annotation,
        )
    else:
        chart.constant_h_data = None

    # Constant specific volume lines:
    if config.chart_params.with_constant_v:
        step = config.chart_params.constant_v_step
        start, end = config.chart_params.range_vol_m3_kg
        chart.constant_v_data = make_constant_specific_volume_lines(
            config.w_min,
            chart.pressure,
            vol_values=np.arange(start, end, step),
            v_label_values=config.chart_params.constant_v_labels,
            style=config.constant_v,
            label_loc=config.chart_params.constant_v_labels_loc,
            family_label=config.chart_params.constant_v_label,
            saturation_curve=chart.saturation,
            dbt_min_seen=dbt_min_seen,
            annotation_style=config.constant_v_annotation,
        )
    else:
        chart.constant_v_data = None

    # Constant wet bulb temperature lines:
    if config.chart_params.with_constant_wet_temp:
        step = config.chart_params.constant_wet_temp_step
        start, end = config.chart_params.range_wet_temp
        chart.constant_wbt_data = make_constant_wet_bulb_temperature_lines(
            dbt_min_seen or config.dbt_min,
            config.dbt_max,
            config.w_min,
            config.w_max,
            chart.pressure,
            wbt_values=np.arange(start, end, step),
            wbt_label_values=config.chart_params.constant_wet_temp_labels,
            style=config.constant_wet_temp,
            label_loc=config.chart_params.constant_wet_temp_labels_loc,
            family_label=config.chart_params.constant_wet_temp_label,
            annotation_style=config.constant_wet_temp_annotation,
        )
    else:
        chart.constant_wbt_data = None


def _gen_chart_zones(config: ChartConfig, chart: PsychroChartModel) -> None:
    # regen all zones
    if config.chart_params.with_zones and not config.chart_params.zones:
        # add default zones
        config.chart_params.zones = DEFAULT_ZONES.zones
    zone_curves = [
        make_zone_curve(
            zone,
            pressure=chart.pressure,
            step_temp=config.limits.step_temp,
            dbt_min=config.dbt_min,
            dbt_max=config.dbt_max,
            w_min=config.w_min,
            w_max=config.w_max,
        )
        for zone in config.chart_params.zones
    ]
    chart.zones = [zc for zc in zone_curves if zc is not None]


def update_psychrochart_data(
    current_chart: PsychroChartModel, config: ChartConfig
) -> None:
    """Update the PsychroChart data with config changes."""
    if config.limits.has_changed:
        current_chart.altitude_m = config.limits.altitude_m
        current_chart.pressure = get_pressure_pa(
            config.limits, current_chart.unit_system_si
        )

    # regen all curves
    current_chart.saturation = make_saturation_line(
        config.dbt_min,
        config.dbt_max,
        config.limits.step_temp,
        current_chart.pressure,
        style=config.saturation,
    )
    _gen_interior_lines(config, current_chart)
    # regen all zones
    _gen_chart_zones(config, current_chart)
    config.commit_changes()
