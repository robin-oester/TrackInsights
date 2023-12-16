"""
This package contains all the ORM models for the database.

The models are used to abstract the database operations.
This allows the system to be used with different databases.
"""
import os

from .athlete import Athlete
from .club import Club
from .discipline import DisciplineConfiguration
from .discipline import Discipline
from .event import Event
from .result import Result
from .log import Log

files = os.listdir(os.path.dirname(__file__))
files.remove("__init__.py")
__all__ = [f[:-3] for f in files if f.endswith(".py")]
