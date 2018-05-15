# -*- coding: utf-8 -*-
"""A library to make psychrometric charts and overlay information in them."""
import json
import os
from time import time
from typing import Callable, Union, Dict, Optional, List, Tuple


PATH_STYLES = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'chart_styles')

DEFAULT_CHART_CONFIG_FILE = os.path.join(
    PATH_STYLES, 'default_chart_config.json')
ASHRAE_CHART_CONFIG_FILE = os.path.join(
    PATH_STYLES, 'ashrae_chart_style.json')
INTERIOR_CHART_CONFIG_FILE = os.path.join(
    PATH_STYLES, 'interior_chart_style.json')
MINIMAL_CHART_CONFIG_FILE = os.path.join(
    PATH_STYLES, 'minimal_chart_style.json')

DEFAULT_ZONES_FILE = os.path.join(
    PATH_STYLES, 'default_comfort_zones.json')

STYLES = {
    "ashrae": ASHRAE_CHART_CONFIG_FILE,
    "default": DEFAULT_CHART_CONFIG_FILE,
    "interior": INTERIOR_CHART_CONFIG_FILE,
    "minimal": MINIMAL_CHART_CONFIG_FILE,
}


def timeit(msg_log: str) -> Callable:
    """Wrap a method to print the execution time of a method call."""
    def real_deco(func) -> Callable:
        def wrapper(*args, **kwargs):
            tic = time()
            out = func(*args, **kwargs)
            print(msg_log + ' TOOK: {:.3f} s'.format(time() - tic))
            return out
        return wrapper
    return real_deco


def _update_config(old_conf: dict, new_conf: dict,
                   verbose: bool=False, recurs_idx: int=0) -> Dict:
    """Update a dict recursively."""
    assert(recurs_idx < 3)
    if old_conf is None:
        return new_conf
    for key, value in old_conf.items():
        if key in new_conf:
            if isinstance(value, dict) and isinstance(new_conf[key], dict):
                new_value = _update_config(
                    old_conf[key], new_conf[key], verbose, recurs_idx + 1)
            else:
                new_value = new_conf[key]
                if verbose and new_value != value:
                    print('Update {}: from {} to {}'
                          .format(key, value, new_value))
            old_conf[key] = new_value
    if recurs_idx > 0:
        old_conf.update({key: new_conf[key] for key in filter(
            lambda x: x not in old_conf, new_conf)})
    return old_conf


def _load_config(new_config: Union[Dict, str]=None,
                 default_config_file: str=None,
                 verbose: bool=False) -> Dict:
    """Load plot parameters from a JSON file."""
    if default_config_file is not None:
        with open(default_config_file) as f:
            config = json.load(f)
    else:
        config = None
    if new_config is not None:
        if isinstance(new_config, str):
            new_config_d = {}  # type: dict
            if new_config.endswith('.json'):
                with open(new_config) as f:
                    new_config_d.update(json.load(f))
            elif new_config in STYLES:
                with open(STYLES[new_config]) as f:
                    new_config_d.update(json.load(f))
            config = _update_config(config, new_config_d, verbose=verbose)
        else:
            assert(isinstance(new_config, dict))
            config = _update_config(config, new_config, verbose=verbose)

    return config


def load_config(styles: Optional[Union[Dict, str]]=None,
                verbose: bool=False) -> Dict:
    """Load the plot params for the psychrometric chart."""
    return _load_config(
        styles, default_config_file=DEFAULT_CHART_CONFIG_FILE,
        verbose=verbose)


def load_zones(zones: Optional[Union[Dict, str]]=DEFAULT_ZONES_FILE,
               verbose: bool=False) -> Dict:
    """Load a zones JSON file to overlay in the psychrometric chart."""
    return _load_config(zones, verbose=verbose)


def iter_solver(initial_value: float, objective_value: float,
                func_eval: Callable, initial_increment: float=4.,
                num_iters_max: int=100, precision: float=0.01) -> float:
    """Solve by iteration."""
    error = 100 * precision
    decreasing = True
    increment = initial_increment
    num_iter = 0
    value_calc = initial_value
    while abs(error) > precision and num_iter < num_iters_max:
        iteration_value = func_eval(value_calc)
        error = objective_value - iteration_value
        if error < 0:
            if not decreasing:
                increment /= 2
                decreasing = True
            increment = max(precision / 10, increment)
            value_calc -= increment
        else:
            if decreasing:
                increment /= 2
                decreasing = False
            increment = max(precision / 10, increment)
            value_calc += increment
        num_iter += 1

        if num_iter >= num_iters_max:
            raise AssertionError(
                'NO CONVERGENCE ERROR AFTER {} ITERATIONS! '
                'Last value: {}, ∆: {}. Objective: {}, iter_value: {}'
                .format(num_iter, value_calc, increment,
                        objective_value, iteration_value))
    return value_calc


def mod_color(color: Union[Tuple, List], modification: float) -> List[float]:
    """Modify color with an alpha value or a darken/lighten percentage."""
    if abs(modification) < .999:  # is alpha level
        color = list(color[:3]) + [modification]
    else:
        color = [max(0., min(1., c * (1 + modification / 100)))
                 for c in color]
    return color


def f_range(start: float, end: float, step: float=1.) -> List[float]:
    """Make list of floats like `numpy.arange`."""
    out = []
    while start < end:
        out.append(start)
        start += step
    return out
