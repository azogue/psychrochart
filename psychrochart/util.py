# -*- coding: utf-8 -*-
"""
A python library to make psychrometric charts and overlay information in them.

"""
import json
from time import time
import os


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


def timeit(msg_log):
    """Wrapper to time a method call."""
    def real_deco(func):
        def wrapper(*args, **kwargs):
            tic = time()
            out = func(*args, **kwargs)
            print(msg_log + ' TOOK: {:.3f} s'.format(time() - tic))
            return out
        return wrapper
    return real_deco


def _update_config(old_conf, new_conf, verbose=False, recurs_idx=0):
    """Update a dict recursively."""
    assert(recurs_idx < 3)
    if old_conf is None:
        return new_conf
    for key, value in old_conf.items():
        if key in new_conf:
            if isinstance(value, dict):
                new_value = _update_config(
                    old_conf[key], new_conf[key], verbose, recurs_idx + 1)
            else:
                new_value = new_conf[key]
                if verbose and new_value != value:
                    print('Update {}: from {} to {}'
                          .format(key, value, new_value))
            old_conf[key] = new_value
    return old_conf


def _load_config(new_config=None, default_config_file=None, verbose=False):
    """Load plot parameters from a JSON file."""
    if default_config_file is not None:
        with open(default_config_file) as f:
            config = json.load(f)
    else:
        config = None
    if new_config is not None:
        if isinstance(new_config, str) and new_config.endswith('.json'):
            with open(new_config) as f:
                new_config = json.load(f)
        elif isinstance(new_config, str) and new_config in STYLES:
            with open(STYLES[new_config]) as f:
                new_config = json.load(f)
        else:
            assert(isinstance(new_config, dict))
            new_config = new_config
        config = _update_config(config, new_config, verbose=verbose)

    return config


def load_config(styles=None, verbose=False):
    """Load the plot params for the psychrometric chart."""
    return _load_config(
        styles, default_config_file=DEFAULT_CHART_CONFIG_FILE,
        verbose=verbose)


def load_zones(zones=DEFAULT_ZONES_FILE, verbose=False):
    """Load a zones JSON file to overlay in the psychrometric chart."""
    return _load_config(zones, verbose=verbose)


def iter_solver(initial_value, objective_value, func_eval,
                initial_increment=4, num_iters_max=100, precision=0.01):
    """Simple solver by iteration."""
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
