import logging
from typing import Any

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
    make_zone_curve,
)
from psychrochart.models.annots import ChartZones, DEFAULT_ZONES
from psychrochart.models.config import ChartConfig, ChartLimits
from psychrochart.models.curves import PsychroChartModel, PsychroCurves
from psychrochart.models.parsers import obj_loader

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


def append_zones_to_chart(
    config: ChartConfig,
    chart: PsychroChartModel,
    zones: ChartZones | dict[str, Any] | str | None = None,
) -> None:
    """Append zones as patches to the psychrometric chart data-container."""
    zones_use = obj_loader(ChartZones, zones, default_obj=DEFAULT_ZONES).zones
    if zones_use:
        curves = PsychroCurves(
            curves=[
                make_zone_curve(zone, config.limits.step_temp, chart.pressure)
                for zone in zones_use
            ]
        )
        chart.zones.append(curves)


def _generate_chart_curves(
    config: ChartConfig, chart: PsychroChartModel, pressure: float
):
    # check chart limits are not fully above the saturation curve!
    assert (chart.saturation.curves[0].y_data > config.w_min).any()
    # check if sat curve cuts x-axis with T > config.dbt_min
    dbt_min_seen: float | None = None
    if chart.saturation.curves[0].y_data[0] < config.w_min:
        temp_sat_interpolator = interp1d(
            chart.saturation.curves[0].y_data,
            chart.saturation.curves[0].x_data,
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
            pressure,
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
            pressure,
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
            pressure,
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
            pressure,
            rh_perc_values=rh_values,
            rh_label_values=config.chart_params.constant_rh_labels,
            style=config.constant_rh,
            label_loc=config.chart_params.constant_rh_labels_loc,
            family_label=config.chart_params.constant_rh_label,
        )
    else:
        chart.constant_rh_data = None

    # Constant enthalpy lines:
    if config.chart_params.with_constant_h:
        step = config.chart_params.constant_h_step
        start, end = config.chart_params.range_h
        chart.constant_h_data = make_constant_enthalpy_lines(
            config.w_min,
            pressure,
            enthalpy_values=np.arange(start, end, step),
            h_label_values=config.chart_params.constant_h_labels,
            style=config.constant_h,
            label_loc=config.chart_params.constant_h_labels_loc,
            family_label=config.chart_params.constant_h_label,
            saturation_curve=chart.saturation.curves[0],
            dbt_min_seen=dbt_min_seen,
        )
    else:
        chart.constant_h_data = None

    # Constant specific volume lines:
    if config.chart_params.with_constant_v:
        step = config.chart_params.constant_v_step
        start, end = config.chart_params.range_vol_m3_kg
        chart.constant_v_data = make_constant_specific_volume_lines(
            config.w_min,
            pressure,
            vol_values=np.arange(start, end, step),
            v_label_values=config.chart_params.constant_v_labels,
            style=config.constant_v,
            label_loc=config.chart_params.constant_v_labels_loc,
            family_label=config.chart_params.constant_v_label,
            saturation_curve=chart.saturation.curves[0],
            dbt_min_seen=dbt_min_seen,
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
            pressure,
            wbt_values=np.arange(start, end, step),
            wbt_label_values=config.chart_params.constant_wet_temp_labels,
            style=config.constant_wet_temp,
            label_loc=config.chart_params.constant_wet_temp_labels_loc,
            family_label=config.chart_params.constant_wet_temp_label,
        )
    else:
        chart.constant_wbt_data = None


def generate_psychrochart(
    config: ChartConfig,
    extra_zones: ChartZones | dict[str, Any] | str | None = None,
    use_unit_system_si: bool = True,
) -> PsychroChartModel:
    """Create the PsychroChart object."""
    # Set unit system for psychrolib and get standard pressure
    pressure = get_pressure_pa(config.limits, use_unit_system_si)

    # base chart with saturation line:
    chart = PsychroChartModel(
        unit_system_si=use_unit_system_si,
        altitude_m=config.limits.altitude_m,
        pressure=pressure,
        saturation=make_saturation_line(
            config.dbt_min,
            config.dbt_max,
            config.limits.step_temp,
            pressure,
            style=config.saturation,
        ),
    )
    _generate_chart_curves(config, chart, pressure)

    if config.chart_params.with_zones:
        append_zones_to_chart(config, chart, extra_zones)

    return chart


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
    _generate_chart_curves(config, current_chart, current_chart.pressure)
    config.commit_changes()
