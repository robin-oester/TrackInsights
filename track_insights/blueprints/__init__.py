import os

from .bestlist_blueprint import bestlist_bp  # noqa: F401
from .disciplines_blueprint import disciplines_bp  # noqa: F401

files = os.listdir(os.path.dirname(__file__))
files.remove("__init__.py")
__all__ = [f[:-3] for f in files if f.endswith(".py")]
