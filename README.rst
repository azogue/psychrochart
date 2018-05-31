It implements a useful collection of
`psychrometric <https://en.wikipedia.org/wiki/Psychrometrics>`_ equations for
moisture and humid air calculations, and the generation of beautiful and high
customizable **psychrometric charts in SVG** with ``matplotlib``.

Calculations are made by implementing experimental equations extracted from
recognized sources, such as the *2009 ASHRAE Handbook—Fundamentals (SI)*.

Install
-------

**Clone it** `from Github <https://github.com/azogue/psychrochart.git>`_ if
you want to run the tests, or simply:

.. code:: bash

    pip install psychrochart

Features
--------

- **SI** units (with temperatures in celsius for better readability).
- Easy style customization with a **JSON template** (colors, line styles
  and line widths).
- Psychrometric charts within temperature and humidity ratio ranges,
  for any pressure, with:

  - **Saturation line**
  - **Constant RH lines**
  - **Constant enthalpy lines**
  - **Constant wet-bulb temperature lines**
  - **Constant specific volume lines**
  - **Constant dry-bulb temperature lines** (internal orthogonal grid, vertical)
  - **Constant humidity ratio lines** (internal orthogonal grid, horizontal)

- Plot legend for each family of lines
- Specify labels for each family of lines
- **Overlay points and zones**
- **Export SVG files**
- Tested against example tables from http://www.engineeringtoolbox.com
- ~100 % code coverage.

The ranges of temperature, humidity and pressure where this library should
provide good results are within the normal environments for people to live in.
Don't expect right results if doing other type of thermodynamic calculations.
Over saturated water vapor states are not implemented.

Changelog
^^^^^^^^^

-  **v0.1.0**: Initial version.
-  **v0.1.1**: Minor plotting fixes, set axis position, define P with ``altitude_m`` or ``pressure_kpa``, reuse plot removing annotations (``chart.remove_annotations``). Axes as internal prop, lazy plotting, save to disk helper (``chart.save``).
-  **v0.1.2**: Add ``agg`` module to set that ``matplotlib`` backend.
-  **v0.1.3**: Add custom params for plotting styles, option to exclude first and last tick (``constant_{humid/temp}_label_include_limits``).
-  **v0.1.4**: Customize labels and its locations for families of psychrometric curves.
-  **v0.1.5**: Add Arrows, compatibility with the Home Assistant component `psychrometrics`.
-  **v0.1.6**: Some cleaning, better typing, flake8, added `tox.ini`.
-  **v0.1.7**: Methods to clean the plot (`.close_fig()`) and to remove the legend (`.remove_legend()`).
-  **v0.1.8**: Memleak with `savefig`.
-  **v0.1.10**: Fix plot limits, do not use pyplot, axes are not optional.
-  **v0.1.11**: Add optional `Axes` as argument for `PsychroChart.plot`.
-  **v0.1.12**: Add empiric equation for wet bulb temperature (@ZhukovGreen contribution).
-  **v0.2.0**: Hide output in verbose mode, better convex hull zones syntax, stable.
-  **v0.2.1**: Make `scipy` an optional requirement (it's only used for the ConvexHull zone).

Usage
-----

.. code:: python

    from psychrochart.chart import PsychroChart
    import matplotlib.pyplot as plt

    axes = PsychroChart().plot(ax=plt.gca())
    plt.show()


Tests
-----

To run the tests, clone the repository and run:

.. code:: bash

    py.test --cov=psychrochart -v --cov-report html

to generate the coverage reports.

License
-------

`MIT license <https://github.com/azogue/psychrochart/blob/master/LICENSE>`_, so do with it as you like ;-)
