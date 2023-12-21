"""
This package contains class related to scraping the swiss-athletics database website.
"""
import os

from .bestlist_field import BestlistField  # noqa: F401
from .processor import Processor  # noqa: F401
from .scrape_config import ScrapeConfig  # noqa: F401
from .scraper import Scraper  # noqa: F401

files = os.listdir(os.path.dirname(__file__))
files.remove("__init__.py")
__all__ = [f[:-3] for f in files if f.endswith(".py")]
