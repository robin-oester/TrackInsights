import argparse
import logging
from typing import Optional

import yaml
from tqdm import tqdm
from track_insights.common import CONFIG_PATH, CONFIG_SCHEMA_PATH, validate_json
from track_insights.common.utils import INVALID_RESULT_SENTINEL
from track_insights.database import DatabaseConnection
from track_insights.database.models import Discipline, DisciplineConfiguration
from track_insights.scores import ScoreList

logging.basicConfig(
    level=logging.NOTSET,
    format="[%(asctime)s]  [%(filename)15s:%(lineno)4d] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    Main function to update the performance scores for the results in the local database.
    """

    parser = argparse.ArgumentParser(description="TrackInsights - Performance Score Updater")

    parser.add_argument("-d", "--discipline", type=str, help="Specify the discipline to update the performance scores.")
    parser.add_argument("--indoor", action="store_true", help="Whether to update indoor events.")
    parser.add_argument("--outdoor", action="store_true", help="Whether to update outdoor events.")
    parser.add_argument("--male", action="store_true", help="Update male events.")
    parser.add_argument("--female", action="store_true", help="Update female events.")

    args = parser.parse_args()

    discipline = args.discipline
    indoor = args.indoor if args.outdoor ^ args.indoor else None
    male = args.male if args.male ^ args.female else None

    logger.info("Checking configuration file and initialize database...")
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config: dict = yaml.safe_load(config_file)
    if not check_configuration(config):
        return

    with DatabaseConnection(config) as database:
        relevant_disciplines = fetch_relevant_disciplines(database, discipline, indoor, male)
        update_scores(database, relevant_disciplines)

    logger.info(f"Updated the scores of {len(relevant_disciplines)} disciplines.")


def update_scores(database: DatabaseConnection, disciplines: list[Discipline]) -> None:
    """
    Update the performance scores for the provided disciplines.

    :param database: The database connection to use.
    :param disciplines: The disciplines to update the scores for.
    """

    with tqdm(disciplines, desc="Disciplines", unit="discipline") as manager:
        for discipline in manager:
            try:
                score_list = ScoreList(discipline)
                for result in discipline.results:
                    if result.ignore:
                        continue

                    result.points = score_list.find_score(result.performance)

                    if result.points == INVALID_RESULT_SENTINEL:
                        result.ignore = True

                database.session.commit()
            except FileNotFoundError as err:
                logger.warning(f"Cannot update scores for discipline {discipline}. Score list was not found: {err}.")


def fetch_relevant_disciplines(
    database: DatabaseConnection, discipline_name: Optional[str], indoor: Optional[bool], male: Optional[bool]
) -> list[Discipline]:
    """
    Fetches the relevant disciplines based on the provided arguments.

    :param database: The database connection to use.
    :param discipline_name: The name of the discipline or all if not provided.
    :param indoor: Whether to fetch indoor disciplines or indoor & outdoor if not provided.
    :param male: Whether to only fetch male disciplines (or both genders if None).
    """

    query = database.session.query(Discipline)

    filters = [Discipline.ignore.is_(False), Discipline.score_identifier.isnot(None)]

    # add filters based on provided arguments
    if discipline_name is not None:
        filters.append(Discipline.config.has(DisciplineConfiguration.name == discipline_name))
    if male is not None:
        filters.append(Discipline.male.is_(male))
    if indoor is not None:
        filters.append(Discipline.indoor.is_(indoor))

    return query.filter(*filters).all()


def check_configuration(config: dict) -> bool:
    valid_yaml, exception = validate_json(config, CONFIG_SCHEMA_PATH)

    if not valid_yaml:
        logger.error(f"Error while validating pipeline configuration file for schema-compliance: {exception.message}")
        logger.error(exception)
        return False

    with DatabaseConnection(config) as database:
        database.create_tables()
    return True


if __name__ == "__main__":
    main()
