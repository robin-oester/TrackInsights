import logging
import time
from typing import Optional

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from seleniumrequests import Chrome
from track_insights.common import ANOMALIES_PATH, current_time_millis
from track_insights.database.models import Discipline
from track_insights.scraping import BASE_URL, BestlistCategory, ScrapeConfig, Scraper
from track_insights.synchronization.bestlist_synchronizer import BestlistSynchronizer
from track_insights.synchronization.synchronization_error import SynchronizationError, SynchronizationErrorType
from track_insights.synchronization.synchronization_statistics import SynchronizationStatistics

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


class DisciplineSynchronizer:
    """
    This class is responsible for scraping all results for a given discipline.
    """

    def __init__(self, config: dict, ignored_entries: set[str], discipline: Discipline, verbose: bool = False) -> None:
        """
        Initialize the scraper.

        :param config: the system configuration.
        :param ignored_entries: the set of ignored records.
        :param discipline: the discipline to scrape.
        """

        self.config = config
        self.ignored_entries = ignored_entries
        self.driver: Optional[Chrome] = None
        self.available_years = Scraper.extract_available_years()

        stripped_name = discipline.config.name.replace(" ", "")
        self.error_file_path = ANOMALIES_PATH / f"{stripped_name}_{current_time_millis()}_errors.json"
        self.discipline = discipline
        self.verbose = verbose

    def __enter__(self) -> "DisciplineSynchronizer":
        """
        Create the driver.

        :return: the opened observer.
        """

        self.driver = self._get_webdriver()
        return self

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb: Exception) -> None:
        """
        Quit from the driver.

        :param exc_type: exception type.
        :param exc_val: exception value.
        :param exc_tb: exception traceback.
        """

        assert self.driver, "No driver available."

        self.driver.quit()

    def scrape_discipline(
        self, start_year: Optional[int] = None, end_year: Optional[int] = None, retry_count: int = 0
    ) -> SynchronizationStatistics:
        """
        Entrypoint for scraping the discipline.

        :param start_year: the start year for scraping.
        :param end_year: the end year for scraping (inclusive).
        :param retry_count: the current retry count.
        """

        if start_year is not None and end_year is not None:
            assert start_year >= end_year, "Start year should be greater or equal to the end year."
        scrape_config = DisciplineSynchronizer.get_basic_config(self.discipline)

        try:
            statistics = self._scrape_all_years(scrape_config, start_year, end_year)
            if self.verbose:
                logger.info(f"Successfully finished processing discipline {self.discipline.config.name}!")
            return statistics
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as err:
            if retry_count >= MAX_RETRIES:
                raise SynchronizationError(
                    f"Scraping discipline {self.discipline.config.name} stopped due to a connection error. {err}",
                    SynchronizationErrorType.CONNECTION_LOST,
                ) from err
            if self.verbose:
                logger.info(f"Connection Error! Retry {retry_count + 1}/{MAX_RETRIES}.")
            return self.scrape_discipline(scrape_config.year, end_year, retry_count + 1)
        except Exception as err:
            raise SynchronizationError(
                f"Scraping discipline {self.discipline.config.name} stopped due to an exception. "
                f"Current scrape config: {scrape_config}. {err}",
                SynchronizationErrorType.UNKNOWN,
            ) from err

    def _scrape_all_years(
        self, scrape_config: ScrapeConfig, start_year: Optional[int], end_year: Optional[int]
    ) -> SynchronizationStatistics:
        """
        Scrape all results for all years.

        :param scrape_config: the scrape configuration.
        :return: the synchronization statistics.
        """

        assert self.driver, "No driver available."
        agg_statistics = SynchronizationStatistics()

        # if no year is specified, we first fetch the results of all years
        if start_year is None:
            scrape_config.year = None
            scrape_config.category = BestlistCategory.ALL_MEN if self.discipline.male else BestlistCategory.ALL_WOMEN
            scrape_config.only_homologated = False

            # if we don't reach the maximum amount of records, we can return
            full_bl, statistics = self._scrape_bestlist(scrape_config)
            agg_statistics.add(statistics)
            if not full_bl:
                return agg_statistics

        scrape_years = self._get_scrape_years(start_year, end_year)
        for year in scrape_years:
            scrape_config.year = year
            scrape_config.category = BestlistCategory.ALL_MEN if self.discipline.male else BestlistCategory.ALL_WOMEN
            scrape_config.only_homologated = False

            # fetch all results for the given year
            full_bl, statistics = self._scrape_bestlist(scrape_config)
            agg_statistics.add(statistics)
            if full_bl:
                statistics = self._scrape_all_categories(scrape_config)
                agg_statistics.add(statistics)
        return agg_statistics

    def _scrape_all_categories(self, scrape_config: ScrapeConfig) -> SynchronizationStatistics:
        """
        Scrape all categories for a given configuration.

        :param scrape_config: the scrape configuration.
        :return: the synchronization statistics.
        """

        assert self.driver, "No driver available."

        agg_statistics = SynchronizationStatistics()
        scrape_config.category = BestlistCategory.MEN if self.discipline.male else BestlistCategory.WOMEN

        # first we scrape for all results (also not homologated)
        scrape_config.only_homologated = False
        full_bl, statistics = self._scrape_bestlist(scrape_config)
        agg_statistics.add(statistics)
        if full_bl:
            # if we reach the maximum amount of records, we load only the homologated results
            statistics = self._scrape_homologated(scrape_config)
            agg_statistics.add(statistics)

        # go through each category one-by-one and load the results
        junior_categories = BestlistCategory.get_junior_categories(self.discipline.male)
        self._setup_exclusive_driver()
        for category in junior_categories:
            scrape_config.category = category
            scrape_config.only_homologated = False
            full_bl, statistics = self._scrape_bestlist(scrape_config)
            agg_statistics.add(statistics)
            if full_bl:
                statistics = self._scrape_homologated(scrape_config)
                agg_statistics.add(statistics)

        # reset the driver in any case
        self.driver.quit()
        self.driver = DisciplineSynchronizer._get_webdriver()
        return agg_statistics

    def _scrape_homologated(self, scrape_config: ScrapeConfig) -> SynchronizationStatistics:
        """
        Only scrape the homologated results.

        :param scrape_config: the scrape configuration.
        """

        scrape_config.only_homologated = True
        full_bl, statistics = self._scrape_bestlist(scrape_config)
        if full_bl:
            logger.warning(f"Found discipline & configuration with full bestlist: {scrape_config}.")
        return statistics

    def _scrape_bestlist(self, scrape_config: ScrapeConfig) -> tuple[bool, SynchronizationStatistics]:
        """
        Scrape the bestlist with the given configuration.

        :param scrape_config: the scrape configuration.
        :return: whether the maximum amount of records was reached.
        """

        scraper = Scraper(scrape_config, self.driver)
        bestlist = scraper.extract_data()

        # check if some data was extracted
        if bestlist is None:
            return False, SynchronizationStatistics()
        processor = BestlistSynchronizer(self.config, scrape_config, bestlist)
        statistics = processor.synchronize(self.error_file_path, self.ignored_entries)

        # check if we reached the maximum amount of records
        if len(bestlist.index) >= scrape_config.amount:
            return True, statistics
        return False, statistics

    def _get_scrape_years(self, start_year: Optional[int], end_year: Optional[int]) -> list[int]:
        """
        Get the years that should be scraped.

        :param start_year: the start year.
        :param end_year: the end year.
        :return: the list of years to scrape.
        """

        filtered_years = []

        if start_year is None and end_year is None:
            return self.available_years

        for year in self.available_years:
            if (start_year is None or year <= start_year) and (end_year is None or year >= end_year):
                filtered_years.append(year)

        return filtered_years

    def _setup_exclusive_driver(self) -> None:
        """
        Set up the driver for exclusive categories.
        """

        assert self.driver, "No driver available."

        time.sleep(1)
        self.driver.find_element(By.ID, "form_anonym:bestlistYear_label").click()
        self.driver.find_element(By.XPATH, "//li[@data-label='2023']").click()
        time.sleep(1)
        self.driver.find_element(By.ID, "form_anonym:bestlistCategory_label").click()
        self.driver.find_element(By.XPATH, "//li[@data-label='U10 Männer']").click()
        time.sleep(1)
        self.driver.find_element(By.ID, "form_anonym:categoryExclusive").click()
        time.sleep(1)

    @staticmethod
    def _get_webdriver() -> Chrome:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # sometimes, this does not work
        driver = Chrome(options=options)
        driver.get(BASE_URL)
        driver.find_element(By.ID, "form_anonym:bestlistType_label").click()
        driver.find_element(By.XPATH, "//li[@data-label='Alle Resultate']").click()
        return driver

    @staticmethod
    def get_basic_config(discipline: Discipline) -> ScrapeConfig:
        return ScrapeConfig(
            category=BestlistCategory.ALL_MEN if discipline.male else BestlistCategory.ALL_WOMEN,
            discipline=discipline,
            year=None,
            allow_wind=True,
            amount=5000,
            only_homologated=False,
        )
