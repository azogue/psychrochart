# Psychrochart

A python 3 library to make **psychrometric charts** and overlay information on them.

It implements a useful collection of psychrometric equations for moisture and humid air calculations, and the generation of beautiful and high customizable **psychrometric charts in SVG** with `matplotlib`.

Calculations are made by implementing experimental equations extracted from recognized sources, such as the _2009 ASHRAE Handbook—Fundamentals (SI)_.

## Install

Get it **[from pypi](https://pypi.python.org/pypi?:action=display&name=psychrochart)** or **[clone it](https://github.com/azogue/psychrochart.git)** if you want to run the tests.

```bash
pip install psychrochart
```

## Features

- **SI** units (with temperatures in celsius for better readability).
- Easy style customization with a **JSON template** (colors, line styles and line widths).
- Psychrometric charts within a temperature range and humidity ratio ranges,
  for any pressure\*, with:
    * **Saturation line**
    * **Constant RH lines**
    * **Constant enthalpy lines**
    * **Constant wet-bulb temperature lines**
    * **Constant specific volume lines**
    * **Constant dry-bulb temperature lines** (internal orthogonal grid, vertical)
    * **Constant humidity ratio lines** (internal orthogonal grid, horizontal)
- **Export SVG files**
- Tested against example tables from [http://www.engineeringtoolbox.com](http://www.engineeringtoolbox.com)
- 100 % code coverage.

\* The ranges of temperature, humidity and pressure where this library should provide good results are within the normal environments for people to live in. Don't expect right results if doing other type of thermodynamic calculations. Over saturated water vapor states are not implemented.

#### TODO list:

- Legends
- **Overlay points**
- Overlay directions (to show evolution in time)
- Zone overlay post plot
- **Docs!**
- contour plot overlay
- **Vectorize** all calc functions.
- Profiling and optimizations with `numba` or `cython` if needed.

#### Changelog

- v0.0.1:   Initial version.

## Chart customization

The default styling for charts is defined in a JSON file that you can change, or you can pass a path of a file in JSON, or a dict, when you create the psychrometric chart. The custom configuration does not need to include all fields, but only the changed ones.

## Tests

To run the tests, clone the repository and run:
```bash
py.test --cov=psychrochart -v --cov-report html
```
to generate the coverage reports.

## License

[MIT license](https://github.com/azogue/psychrochart/blob/master/LICENSE), so do with it as you like ;-)

## Examples

**ASHRAE Handbook black and white style**:

<img src="https://rawgit.com/azogue/psychrochart/master/tests/test_ashrae_psychrochart.svg" width="100%" height="100%">

**Default style**:

<img src="https://rawgit.com/azogue/psychrochart/master/tests/test_default_psychrochart.svg" width="100%" height="100%">

**Minimal style**:

<img src="https://rawgit.com/azogue/psychrochart/master/tests/test_minimal_psychrochart.svg" width="100%" height="100%">

