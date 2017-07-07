# -*- coding: utf-8 -*-
"""
A python library to make psychrometric charts and overlay information in them.

"""
import json
from time import time
import os


basedir = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CHART_CONFIG_FILE = os.path.join(basedir, 'default_chart_config.json')
ASHRAE_CHART_CONFIG_FILE = os.path.join(basedir, 'ashrae_chart_style.json')

STYLES = {
    "ashrae": ASHRAE_CHART_CONFIG_FILE,
    "default": DEFAULT_CHART_CONFIG_FILE,
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
    assert(recurs_idx < 2)
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


def load_config(styles=None, verbose=False):
    """Load the plot params for the psychrometric chart."""
    with open(DEFAULT_CHART_CONFIG_FILE) as f:
        config = json.load(f)
    if styles is not None:
        if isinstance(styles, str) and styles.endswith('.json'):
            with open(styles) as f:
                new_config = json.load(f)
        elif isinstance(styles, str) and styles in STYLES:
            with open(STYLES[styles]) as f:
                new_config = json.load(f)
        else:
            assert(isinstance(styles, dict))
            new_config = styles
        config = _update_config(config, new_config, verbose=verbose)

    return config


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
