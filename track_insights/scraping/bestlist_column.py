from enum import StrEnum  # type: ignore[attr-defined]
from typing import Optional


class BestlistColumn(StrEnum):
    """
    Holds all columns that are available in the bestlist. The values represent the header of each column.
    """

    NUMBER = "Nr"
    ATHLETE = "Name"
    CLUB = "Verein"
    EVENT = "Wettkampf"
    RESULT = "Resultat"
    WIND = "Wind"
    RANK = "Rang"
    NOT_HOMOLOGATED = "NH*"
    NATIONALITY = "Nat."
    BIRTHDATE = "Geb. Dat."
    LOCATION = "Ort"
    DATE = "Datum"
    ATHLETE_CODE = "athlete_code"
    CLUB_CODE = "club_code"
    EVENT_CODE = "event_code"
    ID = "id"

    @staticmethod
    def get_column(header_name: str) -> Optional["BestlistColumn"]:
        """
        Get the column that corresponds to the provided header name.

        :param header_name: the header name to search for.
        :return: the corresponding column or None if not found.
        """

        for field in BestlistColumn:  # type: ignore[attr-defined]
            if field == header_name:
                return field

        # exception: club is defined inconsistently.
        if header_name == "Verein / Schule / Ort":
            return BestlistColumn.CLUB  # type: ignore[return-value]
        return None
