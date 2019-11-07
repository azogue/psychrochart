# -*- coding: utf-8 -*-
"""
Test Cases for psychrometric equations

"""
from unittest import TestCase

from psychrochart.equations import (
    dew_point_temperature,
    enthalpy_moist_air,
    humidity_ratio,
    pressure_by_altitude,
    relative_humidity_from_temps,
    saturation_pressure_water_vapor,
    wet_bulb_temperature,
)
from psychrochart.util import f_range

PRESSURE_STD_ATM_KPA = 101.325

# http://www.engineeringtoolbox.com/water-vapor-saturation-pressure-d_599.html
DRY_TEMP_PSAT_KPA = {
    0: 0.6105,
    5: 0.8722,
    10: 1.228,
    20: 2.338,
    30: 4.243,
    40: 7.376,
    50: 12.33,
    60: 19.92,
    70: 31.16,
    80: 47.34,
    90: 70.10,
    100: 101.3,
}

# http://www.engineeringtoolbox.com/air-altitude-density-volume-d_195.html
ALTITUDE_M_PRESSURE_KPA = {
    0: 101.3,
    75: 100.4,
    150: 99.5,
    250: 98.5,
    300: 97.7,
    450: 95.9,
    600: 94.1,
    750: 92.4,
    900: 90.8,
    1000: 89.1,
    1200: 87.5,
    1350: 85.9,
    1500: 84.3,
    1800: 81.2,
    2100: 78.1,
    2400: 75.2,
}

# http://www.engineeringtoolbox.com/humidity-ratio-air-d_686.html
TEMP_SAT_PRESS_HUMID_RATIO = {
    0: (609.9, 0.003767),
    5: (870, 0.005387),
    10: (1225, 0.007612),
    15: (1701, 0.01062),
    20: (2333, 0.014659),
    25: (3130, 0.019826),
    30: (4234, 0.027125),
}

# http://www.engineeringtoolbox.com/water-vapor-saturation-pressure-air-d_689.html
TEMP_PRESS_PA_DENS_G_KG = {
    0: (603, 5),
    10: (1212, 9),
    20: (2310, 17),
    30: (4195, 30),
    40: (7297, 51),
    50: (12210, 83),
    60: (19724, 130),
    70: (30866, 200),
    80: (46925, 290),
    90: (69485, 420),
    100: (100446, 590),
    120: (196849, 1100),
    140: (358137, 1910),
    160: (611728, 3110),
    180: (990022, 4800),
    200: (1529627, 7110),
}

# fmt: off
# http://www.engineeringtoolbox.com/humidity-measurement-d_561.html
REL_HUMID_WITH_TEMP_WET_DELTA_TEMPS = {
    15: {1: 90, 2: 80, 3: 71, 4: 62, 5: 53, 6: 44, 7: 36, 8: 28, 9: 21, 10: 13},  # noqa E501
    18: {1: 91, 2: 82, 3: 73, 4: 65, 5: 57, 6: 49, 7: 42, 8: 34, 9: 27, 10: 20},  # noqa E501
    20: {1: 91, 2: 83, 3: 75, 4: 67, 5: 59, 6: 52, 7: 45, 8: 38, 9: 31, 10: 25},  # noqa E501
    22: {1: 92, 2: 84, 3: 76, 4: 68, 5: 61, 6: 54, 7: 47, 8: 41, 9: 34, 10: 28},  # noqa E501
    25: {1: 92, 2: 85, 3: 77, 4: 70, 5: 64, 6: 57, 7: 51, 8: 45, 9: 39, 10: 33},  # noqa E501
    27: {1: 92, 2: 85, 3: 78, 4: 71, 5: 65, 6: 59, 7: 53, 8: 47, 9: 41, 10: 36},  # noqa E501
    30: {1: 93, 2: 86, 3: 79, 4: 73, 5: 67, 6: 61, 7: 55, 8: 50, 9: 45, 10: 40},  # noqa E501
    33: {1: 93, 2: 87, 3: 80, 4: 74, 5: 69, 6: 63, 7: 58, 8: 53, 9: 48, 10: 43},  # noqa E501
}
# fmt: on

# http://www.engineeringtoolbox.com/water-vapor-saturation-pressure-air-d_689.html
TEMP_SAT_PRES_DENSITY = {
    0: (603, 0.005),
    10: (1212, 0.009),
    20: (2310, 0.017),
    30: (4195, 0.030),
    40: (7297, 0.051),
    50: (12210, 0.083),
    60: (19724, 0.13),
    70: (30866, 0.20),
    80: (46925, 0.29),
    90: (69485, 0.42),
    100: (100446, 0.59),
    120: (196849, 1.10),
    140: (358137, 1.91),
    160: (611728, 3.11),
    180: (990022, 4.80),
    200: (1529627, 7.11),
}


class TestsPsychrometrics(TestCase):
    """Unit Tests to check the psychrometric equations."""

    pressure_error = 0.5  # kPa
    total_pressure_error = 1.6  # kPa
    total_pressure_error_altitude = 4.0  # kPa

    def _error_compare(self, value, value_ref, max_error, mask_msg):
        self.assertLess(
            abs(value - value_ref),
            max_error,
            mask_msg.format(max_error, value_ref, value),
        )

    def test_press_by_altitude(self):
        """Pressure in kPa from altitude in meters."""
        errors = [
            pressure_by_altitude(alt) - ALTITUDE_M_PRESSURE_KPA[alt]
            for alt in ALTITUDE_M_PRESSURE_KPA
        ]
        self._error_compare(
            sum(errors),
            0,
            self.total_pressure_error_altitude,
            "Pressure for altitude cumulative error > {0} kPa ({1}) -> {2}",
        )

        [
            self._error_compare(
                pressure_by_altitude(alt),
                ALTITUDE_M_PRESSURE_KPA[alt],
                10 * self.pressure_error,
                "Pressure for altitude error> {0} kPa: alt={1} m, est={2}",
            )
            for alt in sorted(ALTITUDE_M_PRESSURE_KPA)
        ]

    def test_relative_humidity_from_temps(self):
        p_atm_kpa = PRESSURE_STD_ATM_KPA

        for dry_temp_c, data in REL_HUMID_WITH_TEMP_WET_DELTA_TEMPS.items():
            for delta_t, obj_rel_humid in data.items():
                wet_temp_c = dry_temp_c - delta_t
                rel_humid_calc = relative_humidity_from_temps(
                    dry_temp_c, wet_temp_c, p_atm_kpa=p_atm_kpa
                )
                self.assertAlmostEqual(
                    round(100 * rel_humid_calc, 1), obj_rel_humid, delta=0.65
                )

    def test_max_specific_humid(self):
        """Max Specific humidity from dry bulb temperature."""
        for t, (ps_ref, xmax_ref) in TEMP_SAT_PRESS_HUMID_RATIO.items():
            psat = saturation_pressure_water_vapor(t)
            xmax = humidity_ratio(psat, PRESSURE_STD_ATM_KPA)
            self.assertAlmostEqual(psat, ps_ref / 1000, delta=0.05)
            self.assertAlmostEqual(xmax, xmax_ref, delta=0.0005)

    def test_enthalpy_moist_air(self):
        """Check the enthalpy of humid air."""
        # From http://www.engineeringtoolbox.com/enthalpy-moist-air-d_683.html
        # Check the enthalpy of humid air at 25ºC with specific
        # moisture content x = 0.0203 kg/kg (saturation).
        press = PRESSURE_STD_ATM_KPA
        dry_temp_c, w_kg_kga = 25, 0.0203

        p_sat = saturation_pressure_water_vapor(dry_temp_c)
        w_max = humidity_ratio(p_sat, press)
        ratio_humid = w_kg_kga / w_max
        p_w_kpa = ratio_humid * p_sat

        h_m = enthalpy_moist_air(dry_temp_c, p_w_kpa, press)
        h_m_bis = enthalpy_moist_air(dry_temp_c, p_w_kpa, press)
        self.assertEqual(h_m, h_m_bis)
        self.assertEqual(round(h_m, 1), 76.9)
        # self.assertEqual(round(h_a, 2), 25.15)
        # self.assertEqual(round(h_v, 1), 0.93 + 50.77)

    def test_press_sat_abs_error(self):
        """Saturation pressure in kPa from dry bulb temperature. Sum error."""
        errors = [
            saturation_pressure_water_vapor(t) - DRY_TEMP_PSAT_KPA[t]
            for t in sorted(DRY_TEMP_PSAT_KPA)
        ]

        self._error_compare(
            sum(errors),
            0,
            self.total_pressure_error,
            "Saturation Pressure error > {0} kPa ({1}) -> {2}",
        )

    def test_press_sat(self):
        """Saturation pressure in kPa from dry bulb temperature."""
        [
            self._error_compare(
                saturation_pressure_water_vapor(t),
                DRY_TEMP_PSAT_KPA[t],
                self.pressure_error * max(0.8, t / 50),
                "M1 - Saturation Pressure error > {} kPa: T={}, est={}",
            )
            for t in sorted(DRY_TEMP_PSAT_KPA)
        ]

    def test_dew_point_temperature(self):
        """Dew point temperature testing."""
        temps = f_range(-20, 60, 1)
        for t in temps:
            p_sat = saturation_pressure_water_vapor(t)
            temp_dp_sat = dew_point_temperature(t, p_sat)
            if temp_dp_sat < 0:
                self.assertAlmostEqual(temp_dp_sat, t, delta=3)
            else:
                self.assertAlmostEqual(temp_dp_sat, t, delta=2.5)

    def test_wet_bulb_temperature(self):
        """Wet bulb temperature from dry bulb temp and relative humidity."""
        p_atm = PRESSURE_STD_ATM_KPA

        for dry_temp_c in f_range(-10, 60, 2.5):
            for relative_humid in f_range(0.05, 1.0001, 0.05):
                wet_temp_c = wet_bulb_temperature(
                    dry_temp_c, relative_humid, p_atm_kpa=p_atm,
                )
                rh_calc = relative_humidity_from_temps(
                    dry_temp_c, wet_temp_c, p_atm_kpa=p_atm
                )
                self.assertAlmostEqual(relative_humid, rh_calc, delta=0.01)

        p_atm = PRESSURE_STD_ATM_KPA * 0.75

        for dry_temp_c in f_range(-5, 50, 5):
            for relative_humid in f_range(0.05, 1.0001, 0.1):
                wet_temp_c = wet_bulb_temperature(
                    dry_temp_c, relative_humid, p_atm_kpa=p_atm,
                )
                rh_calc = relative_humidity_from_temps(
                    dry_temp_c, wet_temp_c, p_atm_kpa=p_atm
                )
                self.assertAlmostEqual(relative_humid, rh_calc, delta=0.01)
