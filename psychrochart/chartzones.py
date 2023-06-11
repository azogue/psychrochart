import numpy as np

from psychrochart.chart_entities import random_internal_value
from psychrochart.chartdata import gen_points_in_constant_relative_humidity
from psychrochart.models.config import ChartZone
from psychrochart.models.curves import PsychroCurve


def _make_zone_delimited_by_vertical_dbt_and_rh(
    zone: ChartZone, pressure: float, *, step_temp: float = 1.0
) -> PsychroCurve:
    assert zone.zone_type == "dbt-rh"
    # points for zone between constant dry bulb temps and RH
    t_min = zone.points_x[0]
    t_max = zone.points_x[-1]
    rh_min = zone.points_y[0]
    rh_max = zone.points_y[-1]
    assert rh_min >= 0.0 and rh_max <= 100.0
    assert t_min < t_max

    temps = np.arange(t_min, t_max + step_temp, step_temp)
    curve_rh_up = gen_points_in_constant_relative_humidity(
        temps, rh_max, pressure
    )
    curve_rh_down = gen_points_in_constant_relative_humidity(
        temps, rh_min, pressure
    )
    abs_humid: list[float] = (
        list(curve_rh_up) + list(curve_rh_down)[::-1] + [curve_rh_up[0]]
    )
    temps_zone: list[float] = list(temps) + list(temps)[::-1] + [temps[0]]
    return PsychroCurve(
        x_data=np.array(temps_zone),
        y_data=np.array(abs_humid),
        style=zone.style,
        type_curve="dbt-rh",
        label=zone.label,
        internal_value=random_internal_value() if zone.label is None else None,
    )


def make_zone_curve(
    zone_conf: ChartZone,
    *,
    pressure: float,
    step_temp: float,
    # dbt_min: float = 0.0,
    # dbt_max: float = 50.0,
    # w_min: float = 0.0,
) -> PsychroCurve | None:
    """Generate plot-points for zone definition."""
    if zone_conf.zone_type == "dbt-rh":
        # points for zone between vertical dbt lines and RH ranges
        return _make_zone_delimited_by_vertical_dbt_and_rh(
            zone_conf, pressure, step_temp=step_temp
        )

    # expect points in plot coordinates!
    assert zone_conf.zone_type == "xy-points"
    zone_value = random_internal_value() if zone_conf.label is None else None
    return PsychroCurve(
        x_data=np.array(zone_conf.points_x),
        y_data=np.array(zone_conf.points_y),
        style=zone_conf.style,
        type_curve="xy-points",
        label=zone_conf.label,
        internal_value=zone_value,
    )
