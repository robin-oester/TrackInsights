import os
import pathlib
from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup, Tag
from track_insights.database.models import Discipline
from track_insights.scraping import BestlistCategory, BestlistColumn, ScrapeConfig, Scraper
from track_insights.scraping.scraper import BASE_URL, EVENT_KEY

DF_PATH = pathlib.Path(os.path.abspath(__file__)).parent.parent / "resources" / "sample_page.html"


def get_sample_discipline() -> Discipline:
    return Discipline(id=1, config_id=1, discipline_code="Test_Discipline", indoor=False, male=True, ignore=False)


def get_sample_config() -> ScrapeConfig:
    return ScrapeConfig(
        year=2023,
        category=BestlistCategory.MEN,
        discipline=get_sample_discipline(),
        allow_wind=True,
        amount=30,
        only_homologated=False,
    )


@patch.object(Scraper, "_silence_loggers")
def test_init(silence_loggers_mock: MagicMock):
    config = get_sample_config()

    mock_driver = MagicMock()
    scraper = Scraper(config, mock_driver)

    assert scraper.scrape_config == config
    silence_loggers_mock.assert_called_once()


def test__extract_code():
    config = get_sample_config()

    mock_driver = MagicMock()
    scraper = Scraper(config, mock_driver)

    html = """
    <td role="gridcell"><a id="form_anonym:5" href="#" onclick="openURLForBestlist('https://www.swiss-athletics.ch/de/wettkampf-bestenliste-neu?&amp;mobile=false&amp;blyear=2023&amp;evt=a21aa-6dqfqu-lik5k1lr-1-liy58dcw-4w2&amp;blcat=M&amp;disci=5c4o3k5m-d686mo-j986g2ie-1-j986ge5c-3mp&amp;top=30&amp;sw=1'); return false;;PrimeFaces.addSubmitParam('form_anonym',{'aeswindowguid':'ba98d03b-e0c1-43a5-fd72-a05130146a60','form_anonym:j_idt88:0:j_idt120':'form_anonym:j_idt88:0:j_idt120'}).submit('form_anonym');return false;PrimeFaces.onPost();">Event</a></td>
    """  # noqa: E501
    parsed_html = BeautifulSoup(html, "html.parser")
    tds: list[Tag] = parsed_html.find_all("td")
    event = scraper._extract_code(tds, 0, EVENT_KEY)

    assert event == "a21aa-6dqfqu-lik5k1lr-1-liy58dcw-4w2"


def test_extract_data():
    config = get_sample_config()

    mock_driver = MagicMock()
    scraper = Scraper(config, mock_driver)
    with open(DF_PATH, "r", encoding="utf-8") as sample_file:
        html = "".join(line.strip() for line in sample_file.read().split("\n"))

    mock_response = MagicMock()
    mock_response.text = html
    with patch.object(scraper.driver, "request", return_value=mock_response) as mock_request:
        dataframe = scraper.extract_data()

        mock_request.assert_called_once_with("GET", BASE_URL, params=config.get_query_arguments(), timeout=10)

    check_array_equality(
        dataframe.columns,
        [
            BestlistColumn.NUMBER,
            BestlistColumn.RESULT,
            BestlistColumn.WIND,
            BestlistColumn.RANK,
            BestlistColumn.ATHLETE,
            BestlistColumn.CLUB,
            BestlistColumn.NATIONALITY,
            BestlistColumn.BIRTHDATE,
            BestlistColumn.EVENT,
            BestlistColumn.LOCATION,
            BestlistColumn.DATE,
            BestlistColumn.ATHLETE_CODE,
            BestlistColumn.CLUB_CODE,
            BestlistColumn.EVENT_CODE,
        ],
    )

    for val in dataframe[BestlistColumn.CLUB_CODE]:
        assert val == "ACC_1.SGALV.1011"
    for val in dataframe[BestlistColumn.ATHLETE_CODE]:
        assert val == "CONTACT.WEB.131887"

    assert dataframe[BestlistColumn.RESULT][0] == "8.32_SR"
    assert dataframe[BestlistColumn.RESULT][1] == "8.22"
    assert dataframe[BestlistColumn.WIND][9] == ""
    assert dataframe[BestlistColumn.WIND][8] == "-0.4"
    assert dataframe[BestlistColumn.RANK][1] == ""

    for idx, val in enumerate(
        zip(
            dataframe[BestlistColumn.ATHLETE],
            dataframe[BestlistColumn.CLUB],
            dataframe[BestlistColumn.EVENT],
            dataframe[BestlistColumn.LOCATION],
            dataframe[BestlistColumn.BIRTHDATE],
            dataframe[BestlistColumn.DATE],
        )
    ):
        assert val[0] == f"Tester_{idx + 1}"
        assert val[1] == f"Club_{idx + 1}"
        assert val[2] == f"Event_{idx + 1}"
        assert val[3] == f"Loc{idx + 1}"
        assert val[4] == f"{idx + 1:02d}.05.1998"
        assert val[5] == f"{idx + 1:02d}.08.2022"


@patch("requests.get")
def test_extract_available_years(requests_mock: MagicMock):
    config = get_sample_config()

    mock_driver = MagicMock()
    scraper = Scraper(config, mock_driver)
    with open(DF_PATH, "r", encoding="utf-8") as sample_file:
        html = "".join(line.strip() for line in sample_file.read().split("\n"))

    mock_response = MagicMock()
    mock_response.text = html
    requests_mock.return_value = mock_response

    check_array_equality(scraper.extract_available_years(), list(range(2023, 1999, -1)))

    requests_mock.assert_called_once_with(BASE_URL, timeout=10)


@patch("requests.get")
def test_extract_disciplines(requests_mock: MagicMock):
    config = get_sample_config()

    mock_driver = MagicMock()
    scraper = Scraper(config, mock_driver)
    with open(DF_PATH, "r", encoding="utf-8") as sample_file:
        html = "".join(line.strip() for line in sample_file.read().split("\n"))

    mock_response = MagicMock()
    mock_response.text = html
    requests_mock.return_value = mock_response

    extracted_disciplines = scraper.extract_disciplines(True, True, 2023)
    assert len(extracted_disciplines) == 92
    assert extracted_disciplines[0] == ("50 m", "5c4o3k5m-d686mo-j986g2ie-1-j986gc6m-1nc")

    params = {
        "lang": "de",
        "mobile": False,
        "blyear": 2023,
        "blcat": "M",
        "indoor": True,
    }

    requests_mock.assert_called_once_with(BASE_URL, params=params, timeout=10)


def check_array_equality(array1: list, array2: list) -> None:
    assert len(array1) == len(array2)

    for idx, val in enumerate(array1):
        assert val == array2[idx]
