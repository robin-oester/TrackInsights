"""This package contains the database classes for the database module.

The models are used to abstract the database operations.
This allows the system to be used with different databases.
"""

import os

from .database_base import DatabaseBase  # noqa: F401
from .database_connection import DatabaseConnection  # noqa: F401

files = os.listdir(os.path.dirname(__file__))
files.remove("__init__.py")
__all__ = [f[:-3] for f in files if f.endswith(".py")]
