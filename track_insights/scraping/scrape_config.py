from dataclasses import dataclass


@dataclass
class ScrapeConfig:
    year: int
    category: str
    male: bool
    discipline_code: str
    indoor: bool
    allow_wind: bool = False
    amount: int = 5000
    allow_nonhomologated: bool = True

    def get_query_arguments(self) -> dict:
        """
        Compute the query arguments build from the config attributes.

        :return: the query arguments as a dict that can be used in a GET-request.
        """
        self._validate_arguments()
        return {
            "lang": "de",
            "mobile": False,
            "blyear": self.year,
            "blcat": self.category,
            "disci": self.discipline_code,
            "indoor": self.indoor,
            "top": self.amount,
            "sw": 1 if self.allow_wind else 0,
            "hom": 1 if self.allow_nonhomologated else 0,
        }

    def _validate_arguments(self) -> None:
        """
        Compute the query arguments build from the config attributes.

        :raise ValueError: whenever an argument does not lie in its domain.
        :return: the query arguments as a dict that can be used in a GET-request.
        """
        if self.amount not in {10, 30, 100, 500, 5000}:
            raise ValueError(f"Amount {self.amount} is invalid.")
