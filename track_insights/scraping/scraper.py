import logging
import re
from urllib.parse import parse_qs, urlparse

import pandas as pd
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from seleniumrequests import Chrome
from track_insights.scraping.bestlist_field import BestlistField
from track_insights.scraping.scrape_config import ScrapeConfig

logger = logging.getLogger(__name__)

ATHLETE_KEY = "con"
CLUB_KEY = "acc"
EVENT_KEY = "evt"


BASE_URL = "https://alabus.swiss-athletics.ch/satweb/faces/bestlist.xhtml"


class Scraper:
    def __init__(self, scrape_config: ScrapeConfig):
        """
        Create a scraper that enables the reading of a particular bestlist page.

        :param scrape_config: the scrape configuration.
        """
        self.scrape_config = scrape_config

        self._silence_loggers()

    # pylint: disable=too-many-locals
    def extract_data(self) -> pd.DataFrame:
        """
        Scrape the bestlist according to the scrape config and return the extracted data as a dataframe.
        The records only contain string type.

        :return: the dataframe of the scraped bestlist.
        """
        parsed_html = self._get_parsed_bestlist()
        table = parsed_html.find("table")
        headers: list[str] = []
        data: list[list[str]] = []
        athlete_index, club_index, event_index = -1, -1, -1
        rows = table.find_all("tr")
        for i, row in enumerate(rows):
            if i == 0:
                header = row.find_all("th")
                for idx, ele in enumerate(header):
                    header_name = ele.text.strip()
                    headers.append(header_name)

                    if header_name == BestlistField.ATHLETE.value:
                        athlete_index = idx
                    elif header_name == BestlistField.CLUB.value:
                        club_index = idx
                    elif header_name == BestlistField.EVENT.value:
                        event_index = idx
                headers.append(BestlistField.ATHLETE_CODE.value)
                headers.append(BestlistField.CLUB_CODE.value)
                headers.append(BestlistField.EVENT_CODE.value)
            else:
                cols = row.find_all("td")
                values = [ele.text.strip() for ele in cols]

                values.append(self._extract_code(cols, athlete_index, ATHLETE_KEY))
                values.append(self._extract_code(cols, club_index, CLUB_KEY))
                values.append(self._extract_code(cols, event_index, EVENT_KEY))
                data.append(values)

        return pd.DataFrame(data, columns=headers, dtype=str)

    def _get_parsed_bestlist(self) -> BeautifulSoup:
        """
        Get the parsed bestlist.

        :return: the bestlist as a parsed html document.
        """
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        driver = Chrome(options=options)
        driver.get(BASE_URL)
        driver.find_element(By.ID, "form_anonym:bestlistType_label").click()
        driver.find_element(By.XPATH, "//li[@data-label='Alle Resultate']").click()

        response = driver.request("GET", BASE_URL, params=self.scrape_config.get_query_arguments())
        driver.quit()

        return BeautifulSoup(response.text, "html.parser")

    @staticmethod
    def _extract_code(columns: list[Tag], index: int, key: str) -> str:
        """
        Extracts the unique identifier (code) from the hyperlink given the key.

        :param columns: the <td> tags with the column values of a row.
        :param index: the index of the column of interest.
        :return: the extracted code.
        """
        first_tag = next(columns[index].children)
        link = re.findall(r"openURLForBestlist\('(.*?)'\)", first_tag["onclick"])[0]

        # parse the url and extract the parameter associated with the key
        parsed_url = urlparse(link)
        return parse_qs(parsed_url.query)[key][0]

    @staticmethod
    def _silence_loggers() -> None:
        logging.getLogger("selenium").setLevel(logging.WARNING)
        logging.getLogger("selenium-requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("filelock").setLevel(logging.WARNING)
