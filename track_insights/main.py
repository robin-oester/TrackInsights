import logging
import os
import pathlib

import yaml
from track_insights.common import validate_yaml
from track_insights.database import DatabaseConnection
from track_insights.database.models import Discipline, DisciplineConfiguration
from track_insights.scraping import Processor, ScrapeConfig, Scraper

logging.basicConfig(
    level=logging.NOTSET,
    format="[%(asctime)s]  [%(filename)15s:%(lineno)4d] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
)
logger = logging.getLogger(__name__)

CONFIG_PATH = pathlib.Path(os.path.abspath(__file__)).parent / "config"
DATA_PATH = pathlib.Path(os.path.abspath(__file__)).parent / "data"


def validate_config_schema(config: dict) -> bool:
    schema_path = CONFIG_PATH / "schema" / "configuration_schema.yaml"
    valid_yaml, exception = validate_yaml(config, schema_path)

    if not valid_yaml:
        logger.error(f"Error while validating pipeline configuration file for schema-compliance: {exception.message}")
        logger.error(exception)
        return False
    return True


def init_database(config: dict) -> None:
    with DatabaseConnection(config) as database:
        database.create_tables()

        # add a sample discipline: longjump, men, outdoor with the correct discipline code.
        if database.session.query(DisciplineConfiguration).filter(DisciplineConfiguration.name == "Weit").count() == 0:
            discipline_config = DisciplineConfiguration(name="Weit", ascending=False)
            discipline = Discipline(
                discipline_code="5c4o3k5m-d686mo-j986g2ie-1-j986ge5c-3mp",
                config=discipline_config,
                indoor=False,
                male=True,
            )
            database.session.add(discipline_config)
            database.session.add(discipline)
            database.session.commit()


def main() -> None:
    config_path = CONFIG_PATH / "configuration.yaml"
    with open(config_path, "r", encoding="utf-8") as config_file:
        config: dict = yaml.safe_load(config_file)
    valid_config = validate_config_schema(config)

    if not valid_config:
        logger.error("System was not able to validate the configuration file.")
        return

    logger.info("Initialize database.")
    init_database(config)

    if not DATA_PATH.exists():
        DATA_PATH.mkdir()

    ignored_entries_path = DATA_PATH / "ignored.json"
    ignored_entries: set[str] = set()
    if not ignored_entries_path.is_file():
        with open(ignored_entries_path, "x", encoding="utf-8") as file:
            file.write("")
    else:
        with open(ignored_entries_path, "r", encoding="utf-8") as file:
            while line := file.readline().strip():
                if line in ignored_entries:
                    logger.warning(f"Duplicate entry '{line}'")
                ignored_entries.add(line)
    logger.info(f"Total ignoring entries: {len(ignored_entries)}")

    logger.info("Start scraping...")
    scrape_config = get_sample_scrape_config(config)
    scraper = Scraper(scrape_config)
    df = scraper.extract_data()
    logger.info("Start processing...")

    error_file_path = DATA_PATH / "errors.json"
    processor = Processor(config, scrape_config, df, ignored_entries)
    processor.process(error_file_path)


def get_sample_scrape_config(config: dict) -> ScrapeConfig:
    with DatabaseConnection(config) as database:
        discipline_config: DisciplineConfiguration = (
            database.session.query(DisciplineConfiguration).filter(DisciplineConfiguration.name == "Weit").first()
        )
        if not discipline_config:
            raise ValueError("Discipline Configuration was not found!")
        disciplines: list[Discipline] = discipline_config.disciplines
    if len(disciplines) == 0:
        raise ValueError("No associated discipline!")
    discipline: Discipline = disciplines[0]

    # scrape the results of 2023, all men ('M'), the 100 best results from the discipline we inserted.
    scrape_config = ScrapeConfig(
        year=2023,
        category="M",
        male=discipline.male,
        discipline_code=discipline.discipline_code,
        indoor=discipline.indoor,
        allow_wind=True,
        amount=10,
        allow_nonhomologated=False,
    )
    return scrape_config


if __name__ == "__main__":
    main()
