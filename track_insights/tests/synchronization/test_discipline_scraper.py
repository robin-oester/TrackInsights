from unittest.mock import MagicMock, patch

from track_insights.database.models import Discipline, DisciplineConfiguration
from track_insights.scraping import BestlistCategory, ScrapeConfig, Scraper
from track_insights.synchronization import BestlistSynchronizer, DisciplineSynchronizer
from track_insights.synchronization.synchronization_statistics import SynchronizationStatistics


def get_sample_discipline() -> Discipline:
    return Discipline(
        id=1,
        config_id=1,
        discipline_code="Test Code",
        indoor=False,
        male=True,
        ignore=False,
        config=DisciplineConfiguration(id=1, name="Test Discipline", ascending=True),
    )


def get_sample_config() -> ScrapeConfig:
    return ScrapeConfig(
        year=2023,
        category=BestlistCategory.MEN,
        discipline=get_sample_discipline(),
        allow_wind=True,
        amount=30,
        only_homologated=False,
    )


def test_discipline_scraper_init():
    # Mock the dependencies
    discipline = get_sample_discipline()
    sample_config = {"key": "value"}
    ignored_entries = {"entry1", "entry2"}

    # Mock the extract_available_years method
    with patch.object(Scraper, "extract_available_years", return_value=[2023, 2022, 2021]) as mock_extract_years:
        discipline_scraper = DisciplineSynchronizer(sample_config, ignored_entries, discipline)

        assert discipline_scraper.config == sample_config
        assert discipline_scraper.ignored_entries == ignored_entries
        assert discipline_scraper.driver is None
        assert discipline_scraper.available_years == [2023, 2022, 2021]
        assert "TestDiscipline" in discipline_scraper.error_file_path.name
        assert discipline_scraper.discipline == discipline

        assert mock_extract_years.called_once()

    mock_driver = MagicMock()
    with patch.object(DisciplineSynchronizer, "_get_webdriver", return_value=mock_driver):
        with DisciplineSynchronizer(sample_config, ignored_entries, discipline) as entered_scraper:
            assert entered_scraper.driver == mock_driver

    mock_driver.quit.assert_called_once()


def test_get_basic_config():
    discipline = get_sample_discipline()
    scrape_config = DisciplineSynchronizer.get_basic_config(discipline)

    assert scrape_config.discipline == discipline
    assert scrape_config.year is None
    assert scrape_config.allow_wind
    assert scrape_config.amount == 5000
    assert not scrape_config.only_homologated


@patch.object(Scraper, "extract_available_years", return_value=[2023, 2022, 2021])
def test__get_scrape_years(extract_available_years_mock: MagicMock):
    discipline = get_sample_discipline()
    discipline_scraper = DisciplineSynchronizer({}, set(), discipline)

    assert discipline_scraper._get_scrape_years(None, None) == [2023, 2022, 2021]
    assert discipline_scraper._get_scrape_years(2022, None) == [2022, 2021]
    assert discipline_scraper._get_scrape_years(None, 2022) == [2023, 2022]
    assert discipline_scraper._get_scrape_years(2022, 2022) == [2022]

    extract_available_years_mock.assert_called_once()


@patch.object(BestlistSynchronizer, "__init__", return_value=None)
@patch.object(BestlistSynchronizer, "synchronize")
def test__scrape_bestlist(synchronize_mock: MagicMock, init_mock: MagicMock):
    discipline = get_sample_discipline()
    discipline_scraper = DisciplineSynchronizer({}, set(), discipline)
    sample_config = get_sample_config()

    with patch.object(Scraper, "extract_data", return_value=None) as extract_data_mock:
        full_bl, _ = discipline_scraper._scrape_bestlist(sample_config)
        assert not full_bl
        init_mock.assert_not_called()
        synchronize_mock.assert_not_called()
        extract_data_mock.assert_called_once()

    bestlist_mock = MagicMock()
    bestlist_mock.index = list(range(30))
    with patch.object(Scraper, "extract_data", return_value=bestlist_mock) as extract_data_mock:
        full_bl, _ = discipline_scraper._scrape_bestlist(sample_config)
        assert full_bl

        extract_data_mock.assert_called_once()
        init_mock.assert_called_once_with(discipline_scraper.config, sample_config, bestlist_mock)
        synchronize_mock.assert_called_once_with(discipline_scraper.error_file_path, discipline_scraper.ignored_entries)

    bestlist_mock.index = []
    with patch.object(Scraper, "extract_data", bestlist_mock) as extract_data_mock:
        full_bl, _ = discipline_scraper._scrape_bestlist(sample_config)
        assert not full_bl
        extract_data_mock.assert_called_once()


@patch.object(DisciplineSynchronizer, "_scrape_bestlist", return_value=(True, None))
def test__scrape_homologated(scrape_bestlist_mock: MagicMock):
    discipline = get_sample_discipline()
    discipline_scraper = DisciplineSynchronizer({}, set(), discipline)
    sample_config = get_sample_config()

    discipline_scraper._scrape_homologated(sample_config)
    scrape_bestlist_mock.assert_called_once_with(sample_config)

    scrape_bestlist_mock.reset_mock()
    sample_config.only_homologated = True
    discipline_scraper._scrape_homologated(sample_config)
    scrape_bestlist_mock.assert_called_once_with(sample_config)


@patch.object(DisciplineSynchronizer, "_setup_exclusive_driver")
@patch.object(DisciplineSynchronizer, "_get_webdriver", return_value=None)
@patch.object(DisciplineSynchronizer, "_scrape_bestlist", return_value=(True, SynchronizationStatistics()))
@patch.object(DisciplineSynchronizer, "_scrape_homologated")
def test__scrape_all_categories(
    scrape_homologated_mock: MagicMock,
    scrape_bestlist_mock: MagicMock,
    webdriver_mock: MagicMock,
    exclusive_driver_mock: MagicMock,
):
    discipline = get_sample_discipline()
    driver_mock = MagicMock()
    discipline_scraper = DisciplineSynchronizer({}, set(), discipline)
    discipline_scraper.driver = driver_mock

    discipline_scraper._scrape_all_categories(get_sample_config())

    assert scrape_bestlist_mock.call_count == len(BestlistCategory.get_junior_categories(True)) + 1
    assert scrape_homologated_mock.call_count == len(BestlistCategory.get_junior_categories(True)) + 1

    exclusive_driver_mock.assert_called_once()
    webdriver_mock.assert_called_once()


@patch.object(DisciplineSynchronizer, "_scrape_all_categories", return_value=SynchronizationStatistics())
@patch.object(DisciplineSynchronizer, "_get_scrape_years", return_value=[2023, 2022, 2021])
def test__scrape_all_years(scrape_years_mock: MagicMock, scrape_all_categories_mock: MagicMock):
    discipline = get_sample_discipline()
    driver_mock = MagicMock()
    discipline_scraper = DisciplineSynchronizer({}, set(), discipline)
    discipline_scraper.driver = driver_mock

    sample_config = get_sample_config()

    with patch.object(
        DisciplineSynchronizer, "_scrape_bestlist", return_value=(False, SynchronizationStatistics())
    ) as scrape_bestlist_mock:
        discipline_scraper._scrape_all_years(sample_config, start_year=None, end_year=None)

        scrape_bestlist_mock.assert_called_once_with(sample_config)
        scrape_years_mock.assert_not_called()

    with patch.object(
        DisciplineSynchronizer, "_scrape_bestlist", return_value=(True, SynchronizationStatistics())
    ) as scrape_bestlist_mock:
        discipline_scraper._scrape_all_years(sample_config, start_year=None, end_year=None)

        scrape_years_mock.assert_called_once_with(None, None)
        assert scrape_bestlist_mock.call_count == 4
        assert scrape_all_categories_mock.call_count == 3
