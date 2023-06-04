"""Common helpers for tests"""
import logging
from pathlib import Path
import re
from time import time
from typing import Callable

from matplotlib import rcParams

_RG_SVGDATE = re.compile(r"(\s+?<dc:date>.*</dc:date>\s+?)")
RSC_EXAMPLES = Path(__file__).parent / "charts"
TEST_BASEDIR = Path(__file__).parent / "generated"


def remove_date_metadata_from_svg(image: Path) -> str:
    """Inplace removal of <dc:date> tag metadata in SVG."""
    # todo finegrain control of svg metadata when saving as SVG
    new_svg = _RG_SVGDATE.sub("\n", image.read_text())
    image.write_text(new_svg)
    return new_svg


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
    TEST_BASEDIR.mkdir(exist_ok=True)
    # set seed for matplotlib 'svg.hashsalt', to generate same ids in SVG
    rcParams["svg.hashsalt"] = "a0576956-8d4f-4e8b-bc5b-7c1effb98147"
