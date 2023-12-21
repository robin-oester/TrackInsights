"""
This package contains all the ORM models for the database.

The models are used to abstract the database operations.
This allows the system to be used with different databases.
"""
import os

from .athlete import Athlete  # noqa: F401
from .club import Club  # noqa: F401
from .discipline import Discipline, DisciplineConfiguration  # noqa: F401
from .event import Event  # noqa: F401
from .log import Log  # noqa: F401
from .result import Result  # noqa: F401

files = os.listdir(os.path.dirname(__file__))
files.remove("__init__.py")
__all__ = [f[:-3] for f in files if f.endswith(".py")]
