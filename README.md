# Psychrochart

A python 3 library to make **[psychrometric charts](https://en.wikipedia.org/wiki/Psychrometrics)** and overlay information on them.

It implements a useful collection of psychrometric equations for moisture and humid air calculations, and the generation of beautiful and high customizable **psychrometric charts in SVG** with `matplotlib`.

Calculations are made by implementing experimental equations extracted from recognized sources, such as the _2009 ASHRAE Handbook—Fundamentals (SI)_.

<img src="https://rawgit.com/azogue/psychrochart/master/tests/chart_overlay_style_minimal.svg" width="100%" height="100%">

## Install

Get it **[from pypi](https://pypi.python.org/pypi?:action=display&name=psychrochart)** or **[clone it](https://github.com/azogue/psychrochart.git)** if you want to run the tests.

```bash
pip install psychrochart
```

## Features

- **SI** units (with temperatures in celsius for better readability).
- Easy style customization with a **JSON template** (colors, line styles and line widths).
- Psychrometric charts within temperature and humidity ratio ranges, for any pressure\*, with:
    * **Saturation line**
    * **Constant RH lines**
    * **Constant enthalpy lines**
    * **Constant wet-bulb temperature lines**
    * **Constant specific volume lines**
    * **Constant dry-bulb temperature lines** (internal orthogonal grid, vertical)
    * **Constant humidity ratio lines** (internal orthogonal grid, horizontal)
- Plot legend for each family of lines
- Specify labels for each family of lines
- **Overlay points and zones**
- **Export SVG files**
- Tested against example tables from [http://www.engineeringtoolbox.com](http://www.engineeringtoolbox.com)
- 100 % code coverage.

\* The ranges of temperature, humidity and pressure where this library should provide good results are within the normal environments for people to live in. Don't expect right results if doing other type of thermodynamic calculations. Over saturated water vapor states are not implemented.

#### TODO list:
- **Better Doc!**
- Overlay directions
- Overlay `pd.Dataframe` time indexed evolution objects
- Zone overlay post plotting
- contour plot overlay
- **Vectorize** all calc functions.
- Profiling and optimizations with `numba` or `cython` if needed.

#### Changelog

- v0.1.0:   Initial version.
- v0.1.1:   Minor plotting fixes, set axis position, define P with `altitude_m` or `pressure_kpa`, reuse plot removing annotations (`chart.remove_annotations`). Axes as internal prop, lazy plotting, save to disk helper (`chart.save`).
- v0.1.2:   Add `agg` module to set that `matplotlib` backend.
- v0.1.3:   Add custom params for plotting styles, option to exclude first and last tick (`constant_{humid/temp}_label_include_limits`).

## Usage

```python
from psychrochart.chart import PsychroChart

# Load default style:
chart_default = PsychroChart()
axes = chart_default.plot()
```

### Chart customization

The default styling for charts is defined in JSON files that you can change, or you can pass a path of a file in JSON, or a dict, when you create the psychrometric chart object.
Included styles are: `default`, `ashrae`, `interior` and `minimal`.

```python
from psychrochart.chart import PsychroChart
from psychrochart.util import load_config

# Load preconfigured styles:
chart_ashrae_style = PsychroChart('ashrae')
chart_ashrae_style.plot()

chart_minimal = PsychroChart('minimal')
chart_minimal.plot()

# Get a preconfigured style dict
dict_config = load_config('interior')

# Specify the styles JSON file:
chart_custom = PsychroChart('/path/to/json_file.json')
chart_custom.plot()

# Pass a dict with the changes wanted:
custom_style = {
    "figure": {
        "figsize": [12, 8],
        "base_fontsize": 12,
        "title": "My chart",
        "x_label": None,
        "y_label": None,
        "partial_axis": False
    },
    "limits": {
        "range_temp_c": [15, 30],
        "range_humidity_g_kg": [0, 25],
        "altitude_m": 900,
        "step_temp": .5
    },
    "saturation": {"color": [0, .3, 1.], "linewidth": 2},
    "constant_rh": {"color": [0.0, 0.498, 1.0, .7], "linewidth": 2.5,
                    "linestyle": ":"},
    "chart_params": {
        "with_constant_rh": True,
        "constant_rh_curves": [25, 50, 75],
        "constant_rh_labels": [25, 50, 75],
        "with_constant_v": False,
        "with_constant_h": False,
        "with_constant_wet_temp": False,
        "with_zones": False
    }
}

chart_custom_2 = PsychroChart(custom_style)
chart_custom_2.plot()
```

The custom configuration does not need to include all fields, but only the fields you want to change.

To play with it and see the results, look at this **[notebook with usage examples](https://github.com/azogue/psychrochart/blob/master/notebooks/Usage%20example%20of%20psychrochart.ipynb)**.

## Tests

To run the tests, clone the repository and run:
```bash
py.test --cov=psychrochart -v --cov-report html
```
to generate the coverage reports.

## License

[MIT license](https://github.com/azogue/psychrochart/blob/master/LICENSE), so do with it as you like ;-)

## Preconfigured styling examples

**Default style**:

<img src="https://rawgit.com/azogue/psychrochart/master/tests/test_default_psychrochart.svg" width="100%" height="100%">

**ASHRAE Handbook black and white style**:

<img src="https://rawgit.com/azogue/psychrochart/master/tests/test_ashrae_psychrochart.svg" width="100%" height="100%">

**Minimal style**:

<img src="https://rawgit.com/azogue/psychrochart/master/tests/test_minimal_psychrochart.svg" width="100%" height="100%">
