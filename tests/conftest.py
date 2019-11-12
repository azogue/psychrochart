"""Common helpers for tests"""
from pathlib import Path

TEST_BASEDIR = Path(__file__).parent / "charts"
TEST_BASEDIR.mkdir(exist_ok=True)
