import os
import pathlib
from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup, Tag
from track_insights.scraping import BestlistField, ScrapeConfig, Scraper
from track_insights.scraping.scraper import EVENT_KEY

DF_PATH = pathlib.Path(os.path.abspath(__file__)).parent / "resources" / "sample_page.html"


def get_sample_config() -> ScrapeConfig:
    return ScrapeConfig(
        year=2023,
        category="M",
        male=True,
        discipline_code="Test_Discipline",
        indoor=False,
        allow_wind=True,
        amount=30,
        allow_nonhomologated=True,
    )


@patch.object(Scraper, "_silence_loggers")
def test_init(silence_loggers_mock: MagicMock):
    config = get_sample_config()
    scraper = Scraper(config)

    assert scraper.scrape_config == config
    silence_loggers_mock.assert_called_once()


def test__extract_code():
    config = get_sample_config()
    scraper = Scraper(config)

    html = """
    <td role="gridcell"><a id="form_anonym:5" href="#" onclick="openURLForBestlist('https://www.swiss-athletics.ch/de/wettkampf-bestenliste-neu?&amp;mobile=false&amp;blyear=2023&amp;evt=a21aa-6dqfqu-lik5k1lr-1-liy58dcw-4w2&amp;blcat=M&amp;disci=5c4o3k5m-d686mo-j986g2ie-1-j986ge5c-3mp&amp;top=30&amp;sw=1'); return false;;PrimeFaces.addSubmitParam('form_anonym',{'aeswindowguid':'ba98d03b-e0c1-43a5-fd72-a05130146a60','form_anonym:j_idt88:0:j_idt120':'form_anonym:j_idt88:0:j_idt120'}).submit('form_anonym');return false;PrimeFaces.onPost();">Event</a></td>
    """  # noqa: E501
    parsed_html = BeautifulSoup(html, "html.parser")
    tds: list[Tag] = parsed_html.find_all("td")
    event = scraper._extract_code(tds, 0, EVENT_KEY)

    assert event == "a21aa-6dqfqu-lik5k1lr-1-liy58dcw-4w2"


@patch("track_insights.scraping.scraper.Scraper._get_parsed_bestlist")
def test_extract_data(parsed_bestlist_mock: MagicMock):
    config = get_sample_config()
    scraper = Scraper(config)
    with open(DF_PATH, "r", encoding="utf-8") as sample_file:
        html = "".join(line.strip() for line in sample_file.read().split("\n"))
    parsed_html = BeautifulSoup(html, "html.parser")
    parsed_bestlist_mock.return_value = parsed_html
    dataframe = scraper.extract_data()
    check_array_equality(
        dataframe.columns,
        [
            "Nr",
            "Resultat",
            "Wind",
            "Rang",
            "Name",
            "Verein",
            "Nat.",
            "Geb. Dat.",
            "Wettkampf",
            "Ort",
            "Datum",
            "athlete_code",
            "club_code",
            "event_code",
        ],
    )

    for val in dataframe[BestlistField.CLUB_CODE.value]:
        assert val == "ACC_1.SGALV.1011"
    for val in dataframe[BestlistField.ATHLETE_CODE.value]:
        assert val == "CONTACT.WEB.131887"

    assert dataframe[BestlistField.RESULT.value][0] == "8.32_SR"
    assert dataframe[BestlistField.RESULT.value][1] == "8.22"
    assert dataframe[BestlistField.WIND.value][9] == ""
    assert dataframe[BestlistField.WIND.value][8] == "-0.4"
    assert dataframe[BestlistField.RANK.value][1] == ""

    for idx, val in enumerate(
        zip(
            dataframe[BestlistField.ATHLETE.value],
            dataframe[BestlistField.CLUB.value],
            dataframe[BestlistField.EVENT.value],
            dataframe[BestlistField.LOCATION.value],
            dataframe[BestlistField.BIRTHDATE.value],
            dataframe[BestlistField.DATE.value],
        )
    ):
        assert val[0] == f"Tester_{idx + 1}"
        assert val[1] == f"Club_{idx + 1}"
        assert val[2] == f"Event_{idx + 1}"
        assert val[3] == f"Loc{idx + 1}"
        assert val[4] == f"{idx + 1:02d}.05.1998"
        assert val[5] == f"{idx + 1:02d}.08.2022"

    parsed_bestlist_mock.assert_called_once()


def check_array_equality(array1: list, array2: list) -> None:
    assert len(array1) == len(array2)

    for idx, val in enumerate(array1):
        assert val == array2[idx]
