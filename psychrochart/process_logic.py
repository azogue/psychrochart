import logging
from typing import Any

import numpy as np
import psychrolib as psy
from psychrolib import GetStandardAtmPressure, IP, SetUnitSystem, SI

from psychrochart.chartdata import (
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
from psychrochart.models.config import ChartConfig
from psychrochart.models.curves import PsychroChartModel, PsychroCurves
from psychrochart.models.parsers import obj_loader

spec_vol_vec = np.vectorize(psy.GetMoistAirVolume)


def set_unit_system(use_unit_system_si: bool = True) -> None:
    """Set unit system for psychrolib."""
    if use_unit_system_si:
        SetUnitSystem(SI)
        logging.info("[SI units mode] ENABLED")
    else:
        SetUnitSystem(IP)
        logging.info("[IP units mode] ENABLED")


def append_zones_to_chart(
    config: ChartConfig,
    chart: PsychroChartModel,
    zones: ChartZones | dict[str, Any] | str | None = None,
) -> None:
    """Append zones as patches to the psychrometric chart data-container."""
    chart.zones.append(
        PsychroCurves(
            curves=[
                make_zone_curve(
                    zone_conf, config.limits.step_temp, chart.pressure
                )
                for zone_conf in obj_loader(
                    ChartZones, zones, default_obj=DEFAULT_ZONES
                ).zones
            ]
        )
    )


def generate_psychrochart(
    config: ChartConfig,
    extra_zones: ChartZones | dict[str, Any] | str | None = None,
    use_unit_system_si: bool = True,
) -> PsychroChartModel:
    """Create the PsychroChart object."""
    # Set unit system for psychrolib and get standard pressure
    altitude_m = -1
    set_unit_system(use_unit_system_si)
    if config.limits.pressure_kpa is not None:
        pressure = config.limits.pressure_kpa * 1000.0  # to Pa
    else:
        altitude_m = config.limits.altitude_m
        pressure = GetStandardAtmPressure(altitude_m)

    # base chart with saturation line:
    chart = PsychroChartModel(
        unit_system_si=use_unit_system_si,
        altitude_m=altitude_m,
        pressure=pressure,
        saturation=make_saturation_line(
            config.dbt_min,
            config.dbt_max,
            config.limits.step_temp,
            pressure,
            style=config.saturation,
        ),
    )

    # Dry bulb constant lines (vertical):
    if config.chart_params.with_constant_dry_temp:
        step = config.chart_params.constant_temp_step
        chart.constant_dry_temp_data = make_constant_dry_bulb_v_lines(
            config.w_min,
            pressure,
            temps_vl=np.arange(config.dbt_min, config.dbt_max, step),
            style=config.constant_dry_temp,
            family_label=config.chart_params.constant_temp_label,
        )

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

    # Constant relative humidity curves:
    if config.chart_params.with_constant_rh:
        chart.constant_rh_data = make_constant_relative_humidity_lines(
            config.dbt_min,
            config.dbt_max,
            config.limits.step_temp,
            pressure,
            rh_perc_values=config.chart_params.constant_rh_curves,
            rh_label_values=config.chart_params.constant_rh_labels,
            style=config.constant_rh,
            label_loc=config.chart_params.constant_rh_labels_loc,
            family_label=config.chart_params.constant_rh_label,
        )

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
        )

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
        )

    # Constant wet bulb temperature lines:
    if config.chart_params.with_constant_wet_temp:
        step = config.chart_params.constant_wet_temp_step
        start, end = config.chart_params.range_wet_temp
        chart.constant_wbt_data = make_constant_wet_bulb_temperature_lines(
            config.dbt_max,
            pressure,
            wbt_values=np.arange(start, end, step),
            wbt_label_values=config.chart_params.constant_wet_temp_labels,
            style=config.constant_wet_temp,
            label_loc=config.chart_params.constant_wet_temp_labels_loc,
            family_label=config.chart_params.constant_wet_temp_label,
        )

    if config.chart_params.with_zones:
        append_zones_to_chart(config, chart, extra_zones)

    return chart
