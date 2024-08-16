import logging
import re
from typing import Optional
from urllib.parse import parse_qs, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag
from seleniumrequests import Chrome
from track_insights.scraping.bestlist_column import BestlistColumn
from track_insights.scraping.scrape_config import ScrapeConfig

logger = logging.getLogger(__name__)

ATHLETE_KEY = "con"
CLUB_KEY = "acc"
EVENT_KEY = "evt"


BASE_URL = "https://alabus.swiss-athletics.ch/satweb/faces/bestlist.xhtml"


class Scraper:
    """
    Scraper class that enables the reading of the bestlist page.
    """

    def __init__(self, scrape_config: ScrapeConfig, driver: Chrome):
        """
        Create a scraper that enables the reading of a particular bestlist page.

        :param scrape_config: the scrape configuration.
        """

        self.scrape_config = scrape_config
        self.driver = driver

        self._silence_loggers()

    @staticmethod
    def extract_available_years() -> list[int]:
        """
        Extract the available years for which results are available.

        :return: list of available years in descending order.
        """

        Scraper._silence_loggers()
        response = requests.get(BASE_URL, timeout=10)
        parsed_page = BeautifulSoup(response.text, "html.parser")
        items = parsed_page.find(attrs={"id": "form_anonym:bestlistYear_input"})

        years: list[int] = []
        elem: Tag
        for elem in items.children:
            try:
                years.append(int(elem.get("value")))
            except ValueError:
                pass
        return sorted(years, reverse=True)

    @staticmethod
    def extract_disciplines(male: bool, indoor: bool, year: Optional[int] = None) -> list[tuple[str, str]]:
        """
        Extract the available disciplines for which results are available.

        :param male: whether we consider male athletes.
        :param indoor: whether we consider indoor results.
        :param year: (Optional) a particular year we consider otherwise we consider them all.
        :return: (name, code)-paris of discipline names and codes.
        """

        Scraper._silence_loggers()
        params = {
            "lang": "de",
            "mobile": False,
            "blyear": "ALL" if year is None else year,
            "blcat": "M" if male else "W",
            "indoor": indoor,
        }
        response = requests.get(BASE_URL, params=params, timeout=10)  # type: ignore
        parsed_page = BeautifulSoup(response.text, "html.parser")
        items = parsed_page.find(attrs={"name": "form_anonym:bestlistDiscipline_input"})

        disciplines: list[tuple[str, str]] = []
        elem: Tag
        for elem in items.children:
            code = elem.get("value")
            if code:
                disciplines.append((elem.text.strip(), code))
        return disciplines

    # pylint: disable=too-many-locals
    def extract_data(self) -> Optional[pd.DataFrame]:
        """
        Scrape the bestlist according to the scrape config and return the extracted data as a dataframe.
        The records only contain string type.

        :return: the dataframe of the scraped bestlist or None, if no results are found.
        """

        response = self.driver.request("GET", BASE_URL, params=self.scrape_config.get_query_arguments(), timeout=10)

        parsed_html = BeautifulSoup(response.text, "html.parser")

        # remove all tooltips
        for div in parsed_html.find_all("div", class_="ui-tooltip ui-widget ui-tooltip-right"):
            div.decompose()  # Remove the element from the DOM

        table = parsed_html.find("table")
        headers: list[BestlistColumn] = []
        data: list[list[str]] = []
        athlete_index, club_index, event_index = -1, -1, -1
        rows = table.find_all("tr")
        for i, row in enumerate(rows):
            if i == 0:
                header = row.find_all("th")
                for idx, ele in enumerate(header):
                    header_name = ele.text.strip()
                    field = BestlistColumn.get_column(header_name)
                    if field is None:
                        raise ValueError(f"Could not find corresponding field of {header_name}.")
                    headers.append(field)

                    if field == BestlistColumn.ATHLETE:
                        athlete_index = idx
                    elif field == BestlistColumn.CLUB:
                        club_index = idx
                    elif field == BestlistColumn.EVENT:
                        event_index = idx
                headers.append(BestlistColumn.ATHLETE_CODE)
                headers.append(BestlistColumn.CLUB_CODE)
                headers.append(BestlistColumn.EVENT_CODE)
            else:
                cols = row.find_all("td")

                # check if there is data available
                if len(headers) - 3 != len(cols):
                    return None

                values = [ele.text.strip() for ele in cols]

                # extract athlete, club and event code
                values.append(self._extract_code(cols, athlete_index, ATHLETE_KEY))
                values.append(self._extract_code(cols, club_index, CLUB_KEY))
                values.append(self._extract_code(cols, event_index, EVENT_KEY))
                data.append(values)

        return pd.DataFrame(data, columns=[header.value for header in headers], dtype=str)

    @staticmethod
    def _extract_code(columns: list[Tag], index: int, key: str) -> str:
        """
        Extracts the unique identifier (code) from the hyperlink given the key.

        :param columns: the <td> tags with the column values of a row.
        :param index: the index of the column of interest.
        :return: the extracted code.
        """

        first_tag = next(iter(columns[index].children))
        link = re.findall(r"openURLForBestlist\('(.*?)'\)", first_tag["onclick"])[0]

        # parse the url and extract the parameter associated with the key
        parsed_url = urlparse(link)
        return parse_qs(parsed_url.query).get(key, [""])[0]

    @staticmethod
    def _silence_loggers() -> None:
        logging.getLogger("selenium").setLevel(logging.WARNING)
        logging.getLogger("selenium-requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("filelock").setLevel(logging.WARNING)
