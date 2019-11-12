# -*- coding: utf-8 -*-
"""A library to make psychrometric charts and overlay information in them."""
import json
import logging
import os
from pathlib import Path
from time import time
from typing import Callable, Dict, List, Optional, Tuple, Union

import numpy as np

NUM_ITERS_MAX = 100

path_styles = Path(__file__).parent / "chart_styles"
DEFAULT_CHART_CONFIG_FILE = str(path_styles / "default_chart_config.json")
ASHRAE_CHART_CONFIG_FILE = str(path_styles / "ashrae_chart_style.json")
ASHRAE_IP_CHART_CONFIG_FILE = str(path_styles / "ashrae_ip_chart_style.json")
INTERIOR_CHART_CONFIG_FILE = str(path_styles / "interior_chart_style.json")
MINIMAL_CHART_CONFIG_FILE = str(path_styles / "minimal_chart_style.json")
DEFAULT_ZONES_FILE = str(path_styles / "default_comfort_zones.json")

STYLES = {
    "ashrae": ASHRAE_CHART_CONFIG_FILE,
    "ashrae_ip": ASHRAE_IP_CHART_CONFIG_FILE,
    "default": DEFAULT_CHART_CONFIG_FILE,
    "interior": INTERIOR_CHART_CONFIG_FILE,
    "minimal": MINIMAL_CHART_CONFIG_FILE,
}

TESTING_MODE = os.getenv("TESTING") is not None


def timeit(msg_log: str) -> Callable:
    """Wrap a method to print the execution time of a method call."""

    def _real_deco(func) -> Callable:
        def _wrapper(*args, **kwargs):
            tic = time()
            out = func(*args, **kwargs)
            logging.info(f"{msg_log} TOOK: {time() - tic:.3f} s")
            return out

        return _wrapper

    return _real_deco


def _update_config(
    old_conf: dict, new_conf: dict, recurs_idx: int = 0
) -> Dict:
    """Update a dict recursively."""
    assert recurs_idx < 3
    if old_conf is None:
        return new_conf
    for key, value in old_conf.items():
        if key in new_conf:
            if isinstance(value, dict) and isinstance(new_conf[key], dict):
                new_value = _update_config(
                    old_conf[key], new_conf[key], recurs_idx + 1
                )
            else:
                new_value = new_conf[key]
            old_conf[key] = new_value
    if recurs_idx > 0:
        old_conf.update(
            {
                key: new_conf[key]
                for key in filter(lambda x: x not in old_conf, new_conf)
            }
        )
    return old_conf


def _load_config(
    new_config: Union[Dict, str] = None, default_config_file: str = None,
) -> Dict:
    """Load plot parameters from a JSON file."""
    if default_config_file is not None:
        with open(default_config_file, encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = None
    if new_config is not None:
        if isinstance(new_config, str):
            new_config_d = {}  # type: dict
            if new_config.endswith(".json"):
                with open(new_config, encoding="utf-8") as f:
                    new_config_d.update(json.load(f))
            elif new_config in STYLES:
                with open(STYLES[new_config], encoding="utf-8") as f:
                    new_config_d.update(json.load(f))
            config = _update_config(config, new_config_d)
        else:
            assert isinstance(new_config, dict)
            config = _update_config(config, new_config)

    return config


def load_config(styles: Optional[Union[Dict, str]] = None) -> Dict:
    """Load the plot params for the psychrometric chart."""
    return _load_config(styles, default_config_file=DEFAULT_CHART_CONFIG_FILE)


def load_zones(zones: Optional[Union[Dict, str]] = DEFAULT_ZONES_FILE) -> Dict:
    """Load a zones JSON file to overlay in the psychrometric chart."""
    return _load_config(zones)


def _iter_solver(
    initial_value: np.ndarray,
    objective_value: np.ndarray,
    func_eval: Callable,
    initial_increment: float = 4.0,
    num_iters_max: int = NUM_ITERS_MAX,
    precision: float = 0.01,
) -> Tuple[float, int]:
    """Solve by iteration."""
    decreasing = True
    increment = initial_increment
    num_iter = 0
    value_calc = initial_value.copy()
    error = objective_value - func_eval(initial_value)
    while abs(error) > precision and num_iter < num_iters_max:
        iteration_value = func_eval(value_calc)
        error = objective_value - iteration_value
        if abs(error) < precision:
            break
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

        if num_iter == num_iters_max:  # pragma: no cover
            raise AssertionError(
                f"No convergence error after {num_iter} iterations! "
                f"Last value: {value_calc}, ∆: {increment}. "
                f"Objective: {objective_value}, iter_value: {iteration_value}"
            )
    return value_calc, num_iter


def solve_curves_with_iteration(
    family_name,
    objective_values: np.ndarray,
    func_init: Callable,
    func_eval: Callable,
) -> np.ndarray:
    """Run the iteration solver for a list of objective values
    for the three types of curves solved with this method."""
    # family:= checking precision | initial_increment | precision
    families = {
        "ENTHALPHY": (0.01, 0.5, 0.01),
        "CONSTANT VOLUME": (0.0005, 1, 0.00025),
    }
    # "CONSTANT VOLUME": (0.0005, 1, 0.00000025, 0.0025, 0.75, 0.00000025),
    if family_name not in families.keys():  # pragma: no cover
        raise AssertionError(
            f"Need a valid family of curves: {list(families.keys())}"
        )

    precision_comp, initial_increment, precision = families[family_name]
    calc_points: List[float] = []
    for objective in objective_values:
        try:
            calc_p, num_iter = _iter_solver(
                np.array(func_init(objective)),
                np.array(objective),
                func_eval=func_eval,
                initial_increment=initial_increment,
                precision=precision,
            )
        except AssertionError as exc:  # pragma: no cover
            logging.error(f"{family_name} CONVERGENCE ERROR: {exc}")
            if TESTING_MODE:
                raise exc
            else:
                return np.array(calc_points)

        if TESTING_MODE and (
            abs(objective - func_eval(calc_p)) > precision_comp
        ):  # pragma: no cover
            msg = (
                f"{family_name} BAD RESULT[#{num_iter}] "
                f"(E={abs(objective - func_eval(calc_p)):.5f}): "
                f"objective: {objective:.5f}, calc_p: {calc_p:.5f}, "
                f"EVAL: {func_eval(calc_p):.5f}"
            )
            logging.error(msg)
            raise AssertionError(msg)
        calc_points.append(calc_p)
    return np.array(calc_points)


def mod_color(color: Union[Tuple, List], modification: float) -> List[float]:
    """Modify color with an alpha value or a darken/lighten percentage."""
    if abs(modification) < 0.999:  # is alpha level
        color = list(color[:3]) + [modification]
    else:
        color = [
            max(0.0, min(1.0, c * (1 + modification / 100))) for c in color
        ]
    return color
