# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2019-11-12

### Added

- Add boolean to switch to IP units
- Add new predefined style "ashrae_ip" in IP units
- Add `pyproject.toml` file and use poetry to manage the package and travis CI

### Changed

- **Rely on `psychrolib` for psychrometric equations**
- Reformat code to adapt to current standards (_black_ and stricter flake8 lint checks)
- Refactor `chart.py` into multiple modules:
  - Move PsychroCurve(s) classes definitions to separate module
  - Rename equations to `.chartdata` and move there all logic for curve data generation
- Adapt tests and do some code cleaning
- Redo internal units for pressure (from kPa to Pa) and enthalpy (from KJ/kg to J/kg) to use IP units
- Adapt plots to use labels, ticks, etc as function of selected unit system.
- Use numpy instead of lists and vectorize psychrometric operations

### Removed

- Own collection of psychrometric equations

## [< 0.2.7] - Old versions changelog

- v0.1.0:   Initial version.
- v0.1.1:   Minor plotting fixes, set axis position, define P with `altitude_m` or `pressure_kpa`, reuse plot removing annotations (`chart.remove_annotations`). Axes as internal prop, lazy plotting, save to disk helper (`chart.save`).
- v0.1.2:   Add `agg` module to set that `matplotlib` backend.
- v0.1.3:   Add custom params for plotting styles, option to exclude first and last tick (`constant_{humid/temp}_label_include_limits`).
- v0.1.4:   Customize labels and its locations for families of psychrometric curves.
- v0.1.5:   Add Arrows, compatibility with the Home Assistant component `psychrometrics`.
- v0.1.6:   Some cleaning, better typing, flake8, added `tox.ini`.
- v0.1.7:   Methods to clean the plot (`.close_fig()`) and to remove the legend (`.remove_legend()`).
- v0.1.8:   Memleak with `savefig`.
- v0.1.10:  Fix plot limits, do not use pyplot, axes are not optional.
- v0.1.11:  Add optional `Axes` as argument for `PsychroChart.plot`.
- v0.1.12:  Add empiric equation for wet bulb temperature (@ZhukovGreen contribution).
- v0.1.13:  Add convex hull option for overlay points.
- v0.2.0:   Hide output in verbose mode, better convex hull zones syntax, stable.
- v0.2.1:   Make `scipy` an optional requirement (it's only used for the ConvexHull zone).
- v0.2.2:   Fix initial conditions for iteration solvers
- v0.2.3:   Handle ConvexHull exception, overlay of series of points.
- v0.2.4:   Set ASHRAE formulation for `saturation_pressure_water_vapor` as default. Minimal adjustments to iteration solvers for enthalpy and specific volume.
- v0.2.5:   Fix coefficient in ASHRAE formulation for `dew_point_temperature`.
- v0.2.6:   Add labels for connectors in chart legend (@@zhang-shen contribution).
