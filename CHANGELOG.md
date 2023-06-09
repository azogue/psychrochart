# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - ♻️ Testing suite refactor + model changes - 2023-06-09

Maintenance-only update, without new features.

##### Changes

- 💥 Remove plotting methods from `PsychroCurve`/`PsychroCurves` for a more functional approach, using methods in `plot_logic.py`
- 💥 Add `PsychroCurve.internal_value` field, to identify the trigger value for each curve (constant H/V/RH...), and evolve validation of data arrays
- ✅ tests: Increase test coverage and optimize tests for faster run (~2x)
- 📦️ env: Add slugify to deps and bump version

## [0.6.0] - ✨ Chart config auto-refresh + bugfixes - 2023-06-07

Before, chart customize was done by creating a new `Psychrochart` object based on some modified chart configuration,
so creating custom plots, or even changing chart limits, was _challenging_ 😓

**Now**, when `chart.config` changes, any call to `chart.save()`, `chart.make_svg()`, or `chart.plot()`
will regenerate the chart data (limits, enabled curves, styling, etc.) before plotting, with only the visible curves inside limits,
(no more 0-size artifacts in SVGs, and most errors because some var is out of range should be gone now 🤞)

##### Changes

- ♻️ Update example notebook with API changes, and using `chart.make_svg()` as the recommended method to generate SVGs
- 💄 **Parse colors into RGBA values**, so "red", "#FF0000", "#FF0000FF" produce the same float repr [1., 0., 0., 1.]
- 🏗️ Add **mutation control for configuration models**, and use it to check if there is any config change before creating a chart, triggering a chart-data regeneration if necessary
- 🔧 Add new field `ChartFigure.dpi` to chart config, for easy customization of matplotlib Figure DPI
- ⚡️ Optimize generation of psychrometric curves inside plot limits

## [0.5.0] - ♻️ Full re-work on internals to use pydantic models - 2023-06-05

🧹 Internal evolution to update the code style to the latest versions and de facto standards, with better typing, input validation, and serialization.
Hardly any new features, but some bug fixes.

### Changes

- 🏗️ Add [`pydantic`](https://docs.pydantic.dev/latest/) models for chart + annotations styling and config, for better (de)serialization and parameter validation.

  New models are:

  - `CurveStyle`, `LabelStyle`, `TickStyle`, `ZoneStyle` := to parse & handle defaults for matplotlib styling parameters
  - `ChartConfig` for the full chart configuration, including sub-models `ChartFigure`, `ChartLimits`, and `ChartParams`, to mirror the old obfuscated config, with the same default values as before
  - `ChartPoint` and `ChartSeries` for styled single-point or array-data annotations
  - `ChartLine` for styled connectors between named points (now without outline 'marker' by default)
  - `ChartArea` for styled convex areas delimited by a list of named points
  - `ChartAnnots` as container for all of the above
  - `ChartZone` (and `ChartZones` as a list), for styled fixed areas (like the default winter/summer comfort zones)

- ♻️ Evolve load methods to parse inputs into pydantic models with _near-zero_ (expected 🤞) breaks when reading old data
- 💥 Rework `PsychroChart` class to work with pydantic `PsychroChartModel`. As the chart is now a pydantic model, there is a `chart.json(...)` method, and loading from serialized data is available with `PsychroChart.parse_file(` / `.validate(` / etc 🤩
  > **BREAKING-CHANGE**: Now the chart creation from a configuration key/file/dict is done with **`PsychroChart.create(config)`**, instead of old `PsychroChart(config)`
- ✨ Add `.make_svg()` method to produce a SVG file as text, and evolve `.save(...)` with optional `canvas_cls: Type[FigureCanvasBase]`, to select kind of matplotlib canvas where to print the chart
- ✨ Support file creation in subfolders with chart.save(dest)
- 🚚 rsc: Deterministic SVG output in tests, and README images without date metadata
- ✅ tests: Adapt API changes in unit tests, remove usages of `unittest.TestCase`, add new tests for pydantic models, annotations, and serialization methods.

## [0.4.0] - ♻️ Maintenance update to upgrade used libraries

### Changes

- 🐛 (from @simplynail in #25): fixing chart setup error with gca() call for recent Matplotlib versions
- 🙈 Add missing .gitignore
- 💥 **Update dependencies + minimal Python version to 3.10** to work with latest releases 🏄
- 🎨 lint: Apply `isort` and `prettier`, and update typing
- 🎨 lint: Evolve pre-commit config with ruff
- 🍱 tests: Update SVG outputs from latest matplotlib
- 🐛 Fix saving PNG with transparent background, by swapping `transparent=True` with `facecolor="none"`
- 🗑️ Use `psychrolib.GetTDryBulbFromMoistAirVolumeAndHumRatio`, removing local method from here, now that it's included there
- 👷 ci: **Swap travis CI config with GH actions to test + publish**

## [0.3.1] - 2019-11-12

### Changed

- Fixed plotting of zones

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

- v0.1.0: Initial version.
- v0.1.1: Minor plotting fixes, set axis position, define P with `altitude_m` or `pressure_kpa`, reuse plot removing annotations (`chart.remove_annotations`). Axes as internal prop, lazy plotting, save to disk helper (`chart.save`).
- v0.1.2: Add `agg` module to set that `matplotlib` backend.
- v0.1.3: Add custom params for plotting styles, option to exclude first and last tick (`constant_{humid/temp}_label_include_limits`).
- v0.1.4: Customize labels and its locations for families of psychrometric curves.
- v0.1.5: Add Arrows, compatibility with the Home Assistant component `psychrometrics`.
- v0.1.6: Some cleaning, better typing, flake8, added `tox.ini`.
- v0.1.7: Methods to clean the plot (`.close_fig()`) and to remove the legend (`.remove_legend()`).
- v0.1.8: Memleak with `savefig`.
- v0.1.10: Fix plot limits, do not use pyplot, axes are not optional.
- v0.1.11: Add optional `Axes` as argument for `PsychroChart.plot`.
- v0.1.12: Add empiric equation for wet bulb temperature (@ZhukovGreen contribution).
- v0.1.13: Add convex hull option for overlay points.
- v0.2.0: Hide output in verbose mode, better convex hull zones syntax, stable.
- v0.2.1: Make `scipy` an optional requirement (it's only used for the ConvexHull zone).
- v0.2.2: Fix initial conditions for iteration solvers
- v0.2.3: Handle ConvexHull exception, overlay of series of points.
- v0.2.4: Set ASHRAE formulation for `saturation_pressure_water_vapor` as default. Minimal adjustments to iteration solvers for enthalpy and specific volume.
- v0.2.5: Fix coefficient in ASHRAE formulation for `dew_point_temperature`.
- v0.2.6: Add labels for connectors in chart legend (@@zhang-shen contribution).
