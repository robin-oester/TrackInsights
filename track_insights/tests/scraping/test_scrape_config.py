from unittest.mock import patch, MagicMock

import pytest

from track_insights.scraping import ScrapeConfig


def test_init():
    scrape_config = ScrapeConfig(
        year=2023,
        category="M",
        male=True,
        discipline_code="Discipline_123",
        indoor=False
    )

    assert scrape_config.year == 2023
    assert scrape_config.category == "M"
    assert scrape_config.male
    assert scrape_config.discipline_code == "Discipline_123"
    assert not scrape_config.indoor
    assert not scrape_config.allow_wind
    assert scrape_config.amount == 5000
    assert scrape_config.allow_nonhomologated


@patch.object(ScrapeConfig, "_validate_arguments")
def test_get_query_arguments(mock_validate_arguments: MagicMock):
    scrape_config = ScrapeConfig(
        year=2023,
        category="M",
        male=True,
        discipline_code="Test",
        indoor=False,
        allow_wind=True,
        amount=500,
        allow_nonhomologated=False)

    query_args = scrape_config.get_query_arguments()
    assert query_args["lang"] == "de"
    assert not query_args["mobile"]
    assert query_args["blyear"] == 2023
    assert query_args["blcat"] == "M"
    assert query_args["disci"] == "Test"
    assert not query_args["indoor"]
    assert query_args["top"] == 500
    assert query_args["sw"] == 1
    assert query_args["hom"] == 0

    mock_validate_arguments.assert_called_once()


def test__validate_arguments():
    scrape_config = ScrapeConfig(
        year=2023,
        category="M",
        male=True,
        discipline_code="Test",
        indoor=False,
    )

    assert scrape_config._validate_arguments() is None

    scrape_config.amount = 500
    assert scrape_config._validate_arguments() is None

    scrape_config.amount = 43
    with pytest.raises(ValueError):
        scrape_config._validate_arguments()
