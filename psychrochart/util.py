import logging
import os
from pathlib import Path
from typing import Callable, Sequence

import numpy as np

NUM_ITERS_MAX = 100
TESTING_MODE = os.getenv("PYTEST_CURRENT_TEST") is not None


def _iter_solver(
    initial_value: np.ndarray,
    objective_value: np.ndarray,
    func_eval: Callable[[np.ndarray | float], float],
    initial_increment: float = 4.0,
    num_iters_max: int = NUM_ITERS_MAX,
    precision: float = 0.01,
) -> tuple[float, int]:
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
            increment = max(precision / 20, increment)
            value_calc -= increment
        else:
            if decreasing:
                increment /= 2
                decreasing = False
            increment = max(precision / 20, increment)
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
    func_init: Callable[[np.ndarray], float],
    func_eval: Callable[[np.ndarray | float], float],
) -> np.ndarray:
    """Run the iteration solver for a list of objective values
    for the three types of curves solved with this method."""
    # family:= checking precision | initial_increment | precision
    families = {
        "ENTHALPHY": (0.01, 0.5, 0.01),
        "CONSTANT VOLUME": (0.0005, 1, 0.00025),
    }
    # "CONSTANT VOLUME": (0.0005, 1, 0.00000025, 0.0025, 0.75, 0.00000025),
    if family_name not in families:  # pragma: no cover
        raise AssertionError(
            f"Need a valid family of curves: {list(families.keys())}"
        )

    precision_comp, initial_increment, precision = families[family_name]
    calc_points: list[float] = []
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


def mod_color(color: Sequence[float], modification: float) -> list[float]:
    """Modify color with an alpha value or a darken/lighten percentage."""
    if abs(modification) < 0.999:  # is alpha level
        color = [*list(color[:3]), modification]
    else:
        color = [
            max(0.0, min(1.0, c * (1 + modification / 100))) for c in color
        ]
    return color


def add_styling_to_svg(
    original: str,
    css_styles: str | Path | None = None,
    svg_definitions: str | None = None,
) -> str:
    """Insert CSS styles and/or SVG definitions under SVG <defs/>."""
    if css_styles is None or svg_definitions is None:
        return original

    insertion_point = original.find("</defs>")
    text_css = (
        css_styles.read_text() if isinstance(css_styles, Path) else css_styles
    )
    return (
        f"{original[:insertion_point]}"
        f"{svg_definitions or ''}\n"
        f'<style type="text/css">\n{text_css}</style>\n'
        f" {original[insertion_point:]}"
    )
