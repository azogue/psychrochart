# -*- coding: utf-8 -*-
"""
Test Cases for psychrometric equations

"""
from unittest import TestCase


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
    100: 101.3
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
    2400: 75.2
}

# http://www.engineeringtoolbox.com/humidity-ratio-air-d_686.html
TEMP_SAT_PRESS_HUMID_RATIO = {
    0: (609.9, 0.003767),
    5: (870, 0.005387),
    10: (1225, 0.007612),
    15: (1701, 0.01062),
    20: (2333, 0.014659),
    25: (3130, 0.019826),
    30: (4234, 0.027125)
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
    200: (1529627, 7110)
}

# http://www.engineeringtoolbox.com/humidity-measurement-d_561.html
REL_HUMID_WITH_TEMP_WET_DELTA_TEMPS = {
 15: {1: 90, 2: 80, 3: 71, 4: 62, 5: 53, 6: 44, 7: 36, 8: 28, 9: 21, 10: 13},
 18: {1: 91, 2: 82, 3: 73, 4: 65, 5: 57, 6: 49, 7: 42, 8: 34, 9: 27, 10: 20},
 20: {1: 91, 2: 83, 3: 75, 4: 67, 5: 59, 6: 52, 7: 45, 8: 38, 9: 31, 10: 25},
 22: {1: 92, 2: 84, 3: 76, 4: 68, 5: 61, 6: 54, 7: 47, 8: 41, 9: 34, 10: 28},
 25: {1: 92, 2: 85, 3: 77, 4: 70, 5: 64, 6: 57, 7: 51, 8: 45, 9: 39, 10: 33},
 27: {1: 92, 2: 85, 3: 78, 4: 71, 5: 65, 6: 59, 7: 53, 8: 47, 9: 41, 10: 36},
 30: {1: 93, 2: 86, 3: 79, 4: 73, 5: 67, 6: 61, 7: 55, 8: 50, 9: 45, 10: 40},
 33: {1: 93, 2: 87, 3: 80, 4: 74, 5: 69, 6: 63, 7: 58, 8: 53, 9: 48, 10: 43}
}

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
    200: (1529627, 7.11)
}


class TestsPsychrometrics(TestCase):
    """Unit Tests to check the psychrometric equations."""

    pressure_error = 0.5  # kPa
    total_pressure_error = 1.6  # kPa
    total_pressure_error_altitude = 4.  # kPa

    def _error_compare(self, value, value_ref, max_error, mask_msg):
        self.assertLess(abs(value - value_ref), max_error,
                        mask_msg.format(max_error, value_ref, value))

    def test_press_by_altitude(self):
        """Pressure in kPa from altitude in meters."""
        from psychrochart.equations import pressure_by_altitude

        errors = [pressure_by_altitude(alt)
                  - ALTITUDE_M_PRESSURE_KPA[alt]
                  for alt in ALTITUDE_M_PRESSURE_KPA]
        self._error_compare(
            sum(errors), 0, self.total_pressure_error_altitude,
            "Pressure for altitude cumulative error > {} kPa ({}) -> {}")

        [self._error_compare(
            pressure_by_altitude(alt),
            ALTITUDE_M_PRESSURE_KPA[alt],
            10 * self.pressure_error,
            "Pressure for altitude error> {} kPa: alt={} m, est={}")
            for alt in sorted(ALTITUDE_M_PRESSURE_KPA)]

    def test_relative_humidity_from_temps(self):
        from psychrochart.equations import (
            relative_humidity_from_temps, PRESSURE_STD_ATM_KPA)

        p_atm_kpa = PRESSURE_STD_ATM_KPA

        for dry_temp_c, data in REL_HUMID_WITH_TEMP_WET_DELTA_TEMPS.items():
            for delta_t, obj_rel_humid in data.items():
                wet_temp_c = dry_temp_c - delta_t
                rel_humid_calc = relative_humidity_from_temps(
                    dry_temp_c, wet_temp_c, p_atm_kpa=p_atm_kpa)
                self.assertAlmostEqual(
                    round(100 * rel_humid_calc, 1), obj_rel_humid,
                    delta=0.65)

    def test_max_specific_humid(self):
        """Max Specific humidity from dry bulb temperature."""
        from psychrochart.equations import (
            humidity_ratio, saturation_pressure_water_vapor)

        for t, (ps_ref, xmax_ref) in TEMP_SAT_PRESS_HUMID_RATIO.items():
            psat = saturation_pressure_water_vapor(t)
            xmax = humidity_ratio(psat)
            # print(t, psat, ps_ref / 1000, xmax, xmax_ref)
            self.assertAlmostEqual(psat, ps_ref / 1000, delta=0.05)
            self.assertAlmostEqual(xmax, xmax_ref, delta=0.0005)

    def test_density_water_vapor(self):
        from psychrochart.equations import (
            density_water_vapor, saturation_pressure_water_vapor)

        for dry_temp_c, (p_sat_ref, d_ref) in TEMP_SAT_PRES_DENSITY.items():
            p_sat_ref /= 1000.  # to kPa
            p_sat = saturation_pressure_water_vapor(dry_temp_c)
            # Check with 5% error at 100 ºC
            self.assertAlmostEqual(
                p_sat, p_sat_ref,
                delta=p_sat_ref / 20 * max(.5, dry_temp_c / 100))

            dens_kg_m3 = density_water_vapor(p_sat, dry_temp_c)
            # print('DBT {} ºC -> {:.3f} (ref: {})  - Err={} %'.format(
            #     dry_temp_c, dens_kg_m3, d_ref,
            #     round(100 * (dens_kg_m3 - d_ref) / d_ref, 1)))
            self.assertAlmostEqual(
                dens_kg_m3, d_ref,
                delta=max(0.005, d_ref / 20) * max(.2, dry_temp_c / 100))

    def test_enthalpy_moist_air(self):
        """Check the enthalpy of humid air."""
        from psychrochart.equations import (
            PRESSURE_STD_ATM_KPA, saturation_pressure_water_vapor,
            humidity_ratio, enthalpy_moist_air)

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

    def test_density_at_saturation(self):
        """Density of saturated humid air from dry bulb temperature."""
        # TODO finish test specific_volume

        # vol_m3_kg = specific_volume(
        #     dry_temp_c, p_sat, p_atm_kpa=PRESSURE_STD_ATM_KPA)
        # print(dry_temp_c, p_sat, p_sat_ref, vol_m3_kg, 1/vol_m3_kg, d_ref)
        # self.assertAlmostEqual(1 / vol_m3_kg, d_ref, delta=1)

        from psychrochart.equations import (
            PRESSURE_STD_ATM_KPA, saturation_pressure_water_vapor,
            specific_volume)

        press = PRESSURE_STD_ATM_KPA
        for t, (ps_ref, dens_ref) in TEMP_PRESS_PA_DENS_G_KG.items():
            # dens_ref_kg_m3 = dens_ref / 1000.

            psat = saturation_pressure_water_vapor(t, mode=1)
            # xmax = humidity_ratio(psat)
            vol_psat = specific_volume(t, psat, p_atm_kpa=press)
            vol_p0 = specific_volume(t, 0, p_atm_kpa=press)
            print('DEB', t, dens_ref, vol_psat, vol_p0, 1/vol_psat, 1/vol_p0)
            dens_kg_m3 = 1 / vol_psat - 1 / vol_p0
            print(dens_kg_m3)

            self.assertAlmostEqual(psat, ps_ref / 1000, delta=27)
            # self.assertAlmostEqual(psat, ps_ref / 1000, delta=0.05)
            # self.assertAlmostEqual(xmax, xmax_ref, delta=0.0005)

    def test_press_sat_abs_error(self):
        """Saturation pressure in kPa from dry bulb temperature. Sum error."""
        from psychrochart.equations import saturation_pressure_water_vapor

        for mode in [1, 2, 3]:
            errors = [saturation_pressure_water_vapor(t, mode=mode)
                      - DRY_TEMP_PSAT_KPA[t]
                      for t in sorted(DRY_TEMP_PSAT_KPA)]

            self._error_compare(
                sum(errors), 0, self.total_pressure_error,
                "Saturation Pressure error > {} kPa ({}) -> {}")

    def test_press_sat_mode_1(self):
        """Saturation pressure in kPa from dry bulb temperature. Mode 1."""
        from psychrochart.equations import saturation_pressure_water_vapor

        mode = 1
        [self._error_compare(
            saturation_pressure_water_vapor(t, mode=mode),
            DRY_TEMP_PSAT_KPA[t], self.pressure_error * max(.8, t / 50),
            "M1 - Saturation Pressure error > {} kPa: T={}, est={}")
            for t in sorted(DRY_TEMP_PSAT_KPA)]

    def test_press_sat_mode_2(self):
        """Saturation pressure in kPa from dry bulb temperature. Mode 2."""
        from psychrochart.equations import saturation_pressure_water_vapor

        mode = 2
        [self._error_compare(
            saturation_pressure_water_vapor(t, mode=mode),
            DRY_TEMP_PSAT_KPA[t], self.pressure_error * max(.8, t / 50),
            "M2 - Saturation Pressure error > {} kPa: T={}, est={}")
            for t in sorted(DRY_TEMP_PSAT_KPA)]

    def test_press_sat_mode_3(self):
        """Saturation pressure in kPa from dry bulb temperature. Mode 3."""
        from psychrochart.equations import saturation_pressure_water_vapor

        mode = 3
        [self._error_compare(
            saturation_pressure_water_vapor(t, mode=mode),
            DRY_TEMP_PSAT_KPA[t], self.pressure_error * max(.8, t / 50),
            "M3 - Saturation Pressure error > {} kPa: T={}, est={}")
            for t in sorted(DRY_TEMP_PSAT_KPA)]

    def test_dew_point_temperature(self):
        """Dew point temperature testing."""
        from psychrochart.equations import (
            saturation_pressure_water_vapor, dew_point_temperature)
        from psychrochart.util import f_range

        temps = f_range(-20, 60, 1)
        for t in temps:
            p_sat = saturation_pressure_water_vapor(t)
            # w_sat = humidity_ratio(p_sat, p_atm_kpa=p_atm)
            temp_dp_sat = dew_point_temperature(p_sat)
            if temp_dp_sat < 0:
                self.assertAlmostEqual(temp_dp_sat, t, delta=3)
            else:
                self.assertAlmostEqual(temp_dp_sat, t, delta=2.5)

    def test_wet_bulb_temperature(self):
        """Wet bulb temperature from dry bulb temp and relative humidity."""
        from psychrochart.equations import (
            wet_bulb_temperature, relative_humidity_from_temps,
            PRESSURE_STD_ATM_KPA)
        from psychrochart.util import f_range

        precision = 0.00001
        p_atm = PRESSURE_STD_ATM_KPA

        for dry_temp_c in f_range(-10, 60, 2.5):
            for relative_humid in f_range(0.05, 1.0001, 0.05):
                wet_temp_c = wet_bulb_temperature(
                    dry_temp_c, relative_humid,
                    p_atm_kpa=p_atm, precision=precision)
                rh_calc = relative_humidity_from_temps(
                    dry_temp_c, wet_temp_c, p_atm_kpa=p_atm)
                # print('wet_temp_c(dbt, rh): {:.3f} ºC ({:.1f} ºC, {:.1f} %)'
                #       .format(wet_temp_c, dry_temp_c, relative_humid * 100))
                self.assertAlmostEqual(relative_humid, rh_calc, delta=0.01)

        precision = 0.00001
        p_atm = PRESSURE_STD_ATM_KPA * .75

        for dry_temp_c in f_range(-5, 50, 5):
            for relative_humid in f_range(0.05, 1.0001, 0.1):
                wet_temp_c = wet_bulb_temperature(
                    dry_temp_c, relative_humid,
                    p_atm_kpa=p_atm, precision=precision)
                rh_calc = relative_humidity_from_temps(
                    dry_temp_c, wet_temp_c, p_atm_kpa=p_atm)
                # print('wet_temp_c(dbt, rh): {:.3f} ºC ({:.1f} ºC, {:.1f} %)'
                #       .format(wet_temp_c, dry_temp_c, relative_humid * 100))
                self.assertAlmostEqual(relative_humid, rh_calc, delta=0.01)

    def test_wet_bulb_temperature_empiric(self):
        """Empiric wet bulb temperature from dry bulb and relative humidity."""
        from psychrochart.equations import (
            wet_bulb_temperature_empiric, wet_bulb_temperature)
        from psychrochart.util import f_range

        for dry_temp_c in f_range(-20, 50, 2.5):
            for relative_humid in f_range(0.05, 1.0001, 0.05):
                wet_temp_c_ref = wet_bulb_temperature(
                    dry_temp_c, relative_humid)
                wet_temp_c = wet_bulb_temperature_empiric(
                    dry_temp_c, relative_humid)
                if -2.33 * dry_temp_c + 28.33 < relative_humid:
                    if abs(wet_temp_c - wet_temp_c_ref) > 1:
                        print('DT: {:.2f}, HR: {:.2f} => WT: [Aprox: {:.2f}, '
                              'Iter: {:.2f} -> ∆: {:.2f}]'.format(
                                dry_temp_c, relative_humid, wet_temp_c,
                                wet_temp_c_ref,
                                abs(wet_temp_c - wet_temp_c_ref)))
                    assert abs(wet_temp_c - wet_temp_c_ref) < 1.5
                else:
                    print('Difference between methods: {:.2f} vs ref={:.2f}'
                          .format(wet_temp_c, wet_temp_c_ref))
                    # out of range
                    assert abs(wet_temp_c - wet_temp_c_ref) > 0.
