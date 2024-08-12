from dataclasses import dataclass
from datetime import date
from typing import Optional

import pandas as pd
from track_insights.common.utils import parse_date, parse_float, parse_result
from track_insights.database.models import Result
from track_insights.scraping import BestlistColumn

MIN_WIND = -100.0
MAX_WIND = 100.0


@dataclass
class Record:
    """
    This class represents a record in the bestlist or in the database.
    """

    performance: int
    wind: Optional[float]
    rank: str
    not_homologated: bool
    athlete: str
    club: str
    nationality: str
    birthdate: date
    event: str
    location: str
    event_date: date
    athlete_code: str
    club_code: str
    event_code: str
    manual: bool = False
    id: Optional[int] = None

    # pylint: disable=too-many-locals
    @classmethod
    def from_dataframe_row(cls, row: pd.Series, columns: set[str]) -> "Record":
        """
        Parses a row from a dataframe to a Record object.

        :param row: row from a dataframe.
        :param columns: column names of the dataframe.
        :return: a new Record object.
        """

        performance = parse_result(row[BestlistColumn.RESULT])
        wind = (parse_float(row[BestlistColumn.WIND])) if BestlistColumn.WIND in columns else None
        rank = row[BestlistColumn.RANK]
        not_homologated = (
            row[BestlistColumn.NOT_HOMOLOGATED] == "X" if BestlistColumn.NOT_HOMOLOGATED in columns else False
        )
        athlete = row[BestlistColumn.ATHLETE]
        club = row[BestlistColumn.CLUB]
        nationality = row[BestlistColumn.NATIONALITY]
        birthdate = parse_date(row[BestlistColumn.BIRTHDATE])
        event = row[BestlistColumn.EVENT]
        location = row[BestlistColumn.LOCATION]
        event_date = parse_date(row[BestlistColumn.DATE])
        athlete_code = row[BestlistColumn.ATHLETE_CODE]
        club_code = row[BestlistColumn.CLUB_CODE]
        event_code = row[BestlistColumn.EVENT_CODE]

        return cls(
            performance=performance,
            wind=wind,
            rank=rank,
            not_homologated=not_homologated,
            athlete=athlete,
            club=club,
            nationality=nationality,
            birthdate=birthdate,
            event=event,
            location=location,
            event_date=event_date,
            athlete_code=athlete_code,
            club_code=club_code,
            event_code=event_code,
        )

    @classmethod
    def from_database_row(cls, result: Result) -> "Record":
        """
        Parses a row from the database to a Record object.

        :param result: row from the database.
        :return: a new Record object.
        """
        return cls(
            performance=result.performance,
            wind=float(result.wind) if result.wind is not None else None,
            rank=result.rank,
            not_homologated=not result.homologated,
            athlete=result.athlete.name,
            club=result.club.name,
            nationality=result.athlete.nationality,
            birthdate=result.athlete.birthdate,
            event=result.event.name,
            location=result.location,
            event_date=result.date,
            athlete_code=result.athlete.athlete_code,
            club_code=result.club.club_code or "",
            event_code=result.event.event_code,
            manual=result.manual,
            id=result.id,
        )

    def is_valid(self) -> bool:
        """
        Checks if the record is valid (i.e., not an anomaly).
        """

        return (
            self.performance >= 0
            and (self.wind is None or MIN_WIND < self.wind < MAX_WIND)
            and self.event_date is not None
            and self.birthdate is not None
            and len(self.nationality) <= 3
        )

    def is_similar(self, other: "Record") -> bool:
        """
        Checks if two records are similar in the sense that they represent the same record.
        """

        similar = (
            self.performance == other.performance
            and self.rank == other.rank
            and self.location == other.location
            and self.event_date == other.event_date
            and self.athlete_code == other.athlete_code
            and self.event_code == other.event_code
            and self.not_homologated == other.not_homologated
        )

        similar &= Record.equal_wind(self.wind, other.wind)
        if self.club_code == "" or other.club_code == "":
            similar &= self.club == other.club
        else:
            similar &= self.club_code == other.club_code

        return similar

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Record):
            return False

        return (
            self.performance == other.performance
            and Record.equal_wind(self.wind, other.wind)
            and self.rank == other.rank
            and self.not_homologated == other.not_homologated
            and self.athlete == other.athlete
            and self.club == other.club
            and self.nationality == other.nationality
            and self.birthdate == other.birthdate
            and self.event == other.event
            and self.location == other.location
            and self.event_date == other.event_date
            and self.athlete_code == other.athlete_code
            and self.club_code == other.club_code
            and self.event_code == other.event_code
        )

    @staticmethod
    def equal_wind(wind1: Optional[float], wind2: Optional[float]) -> bool:
        """
        Checks if two wind values are equal.

        :param wind1: first wind value.
        :param wind2: second wind value.
        :return: True if the wind values are equal, False otherwise.
        """

        if wind1 is None and wind2 is None:
            return True
        if wind1 is not None and wind2 is not None:
            return int(wind1 * 10) == int(wind2 * 10)
        return False
