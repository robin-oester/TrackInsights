from dataclasses import dataclass
from typing import Optional

from track_insights.database.models import Discipline
from track_insights.scraping.bestlist_category import BestlistCategory


@dataclass
class ScrapeConfig:
    """
    Configuration class for scraping the bestlist.
    """

    category: BestlistCategory
    discipline: Discipline
    year: Optional[int] = None
    allow_wind: bool = True
    amount: int = 5000
    only_homologated: bool = False

    def get_query_arguments(self) -> dict:
        """
        Compute the query arguments build from the config attributes.

        :return: the query arguments as a dict that can be used in a GET-request.
        """
        self._validate_arguments()
        return {
            "lang": "de",
            "mobile": False,
            "blyear": self.year if self.year is not None else "all",
            "blcat": self.category.value,
            "disci": self.discipline.discipline_code,
            "indoor": self.discipline.indoor,
            "top": self.amount,
            "sw": 1 if self.allow_wind else 0,
            "hom": 1 if self.only_homologated else 0,
        }

    def _validate_arguments(self) -> None:
        """
        Compute the query arguments build from the config attributes.

        :raise ValueError: whenever an argument does not lie in its domain.
        :return: the query arguments as a dict that can be used in a GET-request.
        """
        if self.amount not in {10, 30, 100, 500, 5000}:
            raise ValueError(f"Amount {self.amount} is invalid.")
