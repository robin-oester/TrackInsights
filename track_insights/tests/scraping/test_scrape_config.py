from unittest.mock import MagicMock, patch

import pytest
from track_insights.database.models import Discipline
from track_insights.scraping import BestlistCategory, ScrapeConfig


def get_sample_discipline() -> Discipline:
    return Discipline(id=1, config_id=1, discipline_code="Test_Discipline", indoor=False, male=True, ignore=False)


def test_init():
    discipline = get_sample_discipline()
    scrape_config = ScrapeConfig(year=2023, category=BestlistCategory.MEN, discipline=discipline)

    assert scrape_config.year == 2023
    assert scrape_config.category == BestlistCategory.MEN
    assert scrape_config.discipline == discipline
    assert scrape_config.allow_wind
    assert scrape_config.amount == 5000
    assert not scrape_config.only_homologated


@patch.object(ScrapeConfig, "_validate_arguments")
def test_get_query_arguments(mock_validate_arguments: MagicMock):
    scrape_config = ScrapeConfig(
        year=2023,
        category=BestlistCategory.ALL_MEN,
        discipline=get_sample_discipline(),
        allow_wind=True,
        amount=500,
        only_homologated=False,
    )

    query_args = scrape_config.get_query_arguments()
    assert query_args["lang"] == "de"
    assert not query_args["mobile"]
    assert query_args["blyear"] == 2023
    assert query_args["blcat"] == "M"
    assert query_args["disci"] == "Test_Discipline"
    assert not query_args["indoor"]
    assert query_args["top"] == 500
    assert query_args["sw"] == 1
    assert query_args["hom"] == 0

    mock_validate_arguments.assert_called_once()


def test__validate_arguments():
    scrape_config = ScrapeConfig(
        year=2023,
        category=BestlistCategory.ALL_MEN,
        discipline=get_sample_discipline(),
    )

    assert scrape_config._validate_arguments() is None

    scrape_config.amount = 500
    assert scrape_config._validate_arguments() is None

    scrape_config.amount = 43
    with pytest.raises(ValueError):
        scrape_config._validate_arguments()
