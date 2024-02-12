"""Common helpers for tests"""

import logging
from pathlib import Path
import re
from time import time
from typing import Callable

from matplotlib import rcParams

from psychrochart import PsychroChart

_RG_SVGDATE = re.compile(r"(\s+?<dc:date>.*</dc:date>\s+?)")
RSC_EXAMPLES = Path(__file__).parent / "example-charts"
TEST_BASEDIR = Path(__file__).parent / "generated"


def store_test_chart(
    chart: PsychroChart,
    name_svg: str,
    png: bool = False,
    svg_rsc: bool = False,
) -> None:
    """Helper method to store test charts."""
    p_svg = TEST_BASEDIR / name_svg
    if png:
        chart.save(p_svg.with_suffix(".png"), facecolor="none")
    if svg_rsc:
        chart.save(RSC_EXAMPLES / name_svg, metadata={"Date": None})
    else:
        chart.save(p_svg, metadata={"Date": None})


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


def pytest_sessionstart(session):
    # set seed for matplotlib 'svg.hashsalt', to generate same ids in SVG
    rcParams["svg.hashsalt"] = "a0576956-8d4f-4e8b-bc5b-7c1effb98147"


# comment to explore generated plots in tests
def pytest_sessionfinish(session):
    from shutil import rmtree

    if TEST_BASEDIR.exists():
        rmtree(TEST_BASEDIR)
