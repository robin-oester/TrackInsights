"""
This package contains class related to computing the performance scores.
"""

import os

from .score_list import ScoreList  # noqa: F401
from .utils import MAX_POINTS, NO_RESULT_SENTINEL, POINTS_IDENTIFIER, RAW_DATA_FOLDER, STORE_FOLDER  # noqa: F401

files = os.listdir(os.path.dirname(__file__))
files.remove("__init__.py")
__all__ = [f[:-3] for f in files if f.endswith(".py")]
