import argparse
import logging

import yaml
from tqdm import tqdm
from track_insights.common import CONFIG_PATH, CONFIG_SCHEMA_PATH, IGNORED_PATH, validate_json
from track_insights.database import DatabaseConnection
from track_insights.synchronization import (
    DisciplineSynchronizer,
    MetadataSynchronizer,
    SynchronizationError,
    SynchronizationStatistics,
)
from track_insights.synchronization.synchronization_error import SynchronizationErrorType

logging.basicConfig(
    level=logging.NOTSET,
    format="[%(asctime)s]  [%(filename)15s:%(lineno)4d] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
)
logger = logging.getLogger(__name__)

MAX_UNKNOWN_ERRORS = 5


# pylint: disable=too-many-locals,too-many-statements
def main() -> None:
    """
    Main function to start the TrackInsights application with optional filters.
    """

    parser = argparse.ArgumentParser(description="TrackInsights - Performance Data Scraper")

    parser.add_argument("-d", "--discipline", type=str, help="Specify the discipline to filter results.")
    parser.add_argument("--indoor", action="store_true", help="Filter results to indoor events.")
    parser.add_argument("--outdoor", action="store_true", help="Filter results to outdoor events.")
    parser.add_argument("--year", type=int, help="Specify the year to filter results.")
    parser.add_argument("--male", action="store_true", help="Filter results to male athletes.")
    parser.add_argument("--female", action="store_true", help="Filter results to female athletes.")
    parser.add_argument("--log_deletions", action="store_true", help="Log deleted records.")

    args = parser.parse_args()

    discipline = args.discipline
    indoor = args.indoor if args.outdoor ^ args.indoor else None
    male = args.male if args.male ^ args.female else None
    year = args.year

    # check the configuration
    logger.info("Checking configuration file and initialize database...")
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config: dict = yaml.safe_load(config_file)
    if not check_configuration(config):
        return

    # load ignored records
    ignored_entries: set[str] = set()
    with open(IGNORED_PATH, "r", encoding="utf-8") as file:
        while line := file.readline().strip():
            if line in ignored_entries:
                logger.warning(f"Duplicate entry '{line}'")
            ignored_entries.add(line)

    logger.info(f"Loaded {len(ignored_entries)} entries to be ignored.")

    # Print the received arguments to verify
    logger.info("Starting TrackInsights with the following filters:")
    logger.info(f"Discipline: {'All' if discipline is None else discipline}")
    logger.info(f"Year: {year if year else 'All'}")
    logger.info(f"Place: {('Indoor' if indoor else 'Outdoor') if indoor is not None else 'Indoor & Outdoor'}")
    logger.info(f"Gender: {('Male' if male else 'Female') if male is not None else 'Any'}")

    metadata_manager = MetadataSynchronizer(config)
    metadata_manager.check_disciplines()

    disciplines = metadata_manager.get_all_disciplines(discipline, year, indoor, male)

    if len(disciplines) > 0:
        logger.info(f"Found {len(disciplines)} discipline(s) to fetch.")
        statistics = SynchronizationStatistics()
        num_errors = 0
        with tqdm(disciplines, desc="Disciplines", unit="discipline") as manager:
            for discipline in manager:
                try:
                    with DisciplineSynchronizer(config, ignored_entries, discipline) as scraper:
                        statistics.add(scraper.scrape_discipline(start_year=year, end_year=year))
                except SynchronizationError as err:
                    logger.warning(err.message)
                    if err.error_type == SynchronizationErrorType.UNKNOWN:
                        if num_errors > MAX_UNKNOWN_ERRORS:
                            logger.error("Too many unknown errors. Stopping the fetcher.")
                            break
                        num_errors += 1
                    else:
                        logger.error("Connection error. Stopping the fetcher.")
                        break
        logger.info("Fetcher Summary:")
        logger.info(f"Inserted Records: {statistics.added_records}")
        logger.info(f"Inserted Athletes: {statistics.added_athletes}")
        logger.info(f"Inserted Clubs: {statistics.added_clubs}")
        logger.info(f"Inserted Events: {statistics.added_events}")
        logger.info(f"Updates: {statistics.updates}")
        logger.info(f"Deletions: {len(statistics.deletions)}")

        if args.log_deletions and len(statistics.deletions) > 0:
            logger.info("The following records were deleted:")
            for record in statistics.deletions:
                logger.info(record)
    else:
        logger.info("No disciplines to fetch.")


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
