import logging
from typing import Optional

from track_insights.database import DatabaseConnection
from track_insights.database.models import Discipline, DisciplineConfiguration, DisciplineType
from track_insights.scraping import Scraper

logger = logging.getLogger(__name__)


class MetadataSynchronizer:
    """
    This class implements functions related to the synchronization of metadata between the database and the bestlist.
    It is responsible for checking if all disciplines are registered and for fetching disciplines.
    """

    def __init__(self, config: dict):
        self.config = config

    def check_disciplines(self, year: Optional[int] = None) -> None:
        """
        Check if all disciplines are registered in the database by comparing to the results of the bestlist.
        If not, they are added.

        :param year: year to check disciplines (ALL if not provided).
        """

        with DatabaseConnection(self.config) as database:
            for male in [True, False]:
                for indoor in [True, False]:
                    disciplines = Scraper.extract_disciplines(male, indoor, year)
                    for discipline, code in disciplines:
                        # if discipline code not in database, it gets added
                        if (
                            database.session.query(Discipline)
                            .filter(
                                Discipline.discipline_code == code,
                                Discipline.male.is_(male),
                                Discipline.indoor.is_(indoor),
                            )
                            .first()
                            is None
                        ):
                            config = (
                                database.session.query(DisciplineConfiguration)
                                .filter(DisciplineConfiguration.name == discipline)
                                .first()
                            )
                            if config is None:
                                # add the discipline configuration
                                config = DisciplineConfiguration(
                                    name=discipline, discipline_type=DisciplineType.SHORT_TRACK
                                )  # default
                                database.session.add(config)

                                logger.info(f"Insert new discipline configuration: '{discipline}'.")

                            # add the discipline
                            db_discipline = Discipline(config=config, discipline_code=code, indoor=indoor, male=male)
                            database.session.add(db_discipline)

                            logger.info(f"Insert new discipline object belonging to '{discipline}'.")
            database.session.commit()

    # pylint: disable=too-many-locals
    def get_all_disciplines(
        self,
        discipline_name: Optional[str] = None,
        year: Optional[int] = None,
        indoor: Optional[bool] = None,
        male: Optional[bool] = None,
    ) -> list[Discipline]:
        """
        Fetch all disciplines that match the provided filters. We differentiate between two cases:
        - the first one considers a particular year (year is not None). In this scenario, we extract the disciplines
          for which results are available in this year. This significantly reduces the amount of disciplines
          to scrape. It is therefore optimized for regular execution.
        - the second case considers all disciplines in the database. This is useful for one-time operations or to create
          a backup of the bestlist.

        :param discipline_name: discipline name to filter or ALL if not provided.
        :param year: year to filter disciplines (ALL if not provided).
        :param indoor: filter by indoor or outdoor results (Both if not provided).
        :param male: whether to only consider male athletes (Both genders if not provided).
        :return: list of all disciplines that match the provided filters.
        """

        if year is not None and discipline_name is None:
            assert year in Scraper.extract_available_years(), f"Results for year {year} are not available"

            place_filter = [True, False] if indoor is None else [indoor]
            gender_filter = [True, False] if male is None else [male]
            disciplines: list[Discipline] = []
            with DatabaseConnection(self.config) as database:
                for indoor_val in place_filter:
                    for male_val in gender_filter:
                        for name, code in Scraper.extract_disciplines(male_val, indoor_val, year):
                            discipline: Optional[Discipline] = (
                                database.session.query(Discipline)
                                .filter(
                                    Discipline.discipline_code == code,
                                    Discipline.indoor.is_(indoor_val),
                                    Discipline.male.is_(male_val),
                                )
                                .first()
                            )
                            if discipline is None:
                                raise ValueError(f"Discipline with name {name} and code {code} is not registered!")
                            if not discipline.ignore:
                                disciplines.append(discipline)
            return disciplines

        with DatabaseConnection(self.config) as database:
            filters = [Discipline.ignore.is_(False)]

            # add filters based on provided arguments
            if discipline_name is not None:
                filters.append(Discipline.config.has(DisciplineConfiguration.name == discipline_name))
            if male is not None:
                filters.append(Discipline.male.is_(male))
            if indoor is not None:
                filters.append(Discipline.indoor.is_(indoor))

            return database.session.query(Discipline).filter(*filters).all()
