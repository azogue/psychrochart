"""Common helpers for tests"""
import logging
from pathlib import Path
from time import time
from typing import Callable

from matplotlib import rcParams

TEST_BASEDIR = Path(__file__).parent / "charts"
TEST_BASEDIR.mkdir(exist_ok=True)


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
