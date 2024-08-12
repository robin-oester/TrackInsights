import os
import pathlib
import tempfile
from datetime import date

import pandas as pd
from track_insights.database import DatabaseConnection
from track_insights.database.models import Athlete, Club, Discipline, DisciplineConfiguration, Event, Result
from track_insights.scraping import BestlistCategory, ScrapeConfig
from track_insights.synchronization import BestlistSynchronizer, Record, RecordCollection

DATABASE = pathlib.Path(os.path.abspath(__file__)).parent / "test_bestlist_synchronizer.database"
DF_PATH = pathlib.Path(os.path.abspath(__file__)).parent.parent / "resources" / "sample_dataframe.csv"


def get_minimal_config() -> dict:
    return {
        "database": {
            "drivername": "sqlite",
            "username": "",
            "password": "",
            "host": "",
            "port": 0,
            "database": f"{DATABASE}",
        }
    }


def setup_function():
    DATABASE.unlink(True)

    with DatabaseConnection(get_minimal_config()) as database:
        database.create_tables()

        athlete = Athlete(
            athlete_code="Athlete_1",
            name="Max Mustermann",
            birthdate=date.fromisoformat("2000-02-15"),
            nationality="SUI",
            latest_date=date.fromisoformat("2023-01-11"),
        )

        club = Club(club_code="Club_1", name="LV Muster", latest_date=date.fromisoformat("2023-01-11"))

        discipline_config = DisciplineConfiguration(
            name="Weit",
            ascending=False,
        )

        discipline = Discipline(
            discipline_code="Discipline_1",
            config=discipline_config,
            indoor=False,
            male=True,
        )

        event = Event(event_code="Event_1", name="Test Event", latest_date=date.fromisoformat("2023-01-11"))

        database.session.add(athlete)
        database.session.add(club)
        database.session.add(discipline_config)
        database.session.add(discipline)
        database.session.add(event)
        database.session.commit()


def teardown_function():
    DATABASE.unlink()


def get_scrape_config() -> ScrapeConfig:
    with DatabaseConnection(get_minimal_config()) as database:
        discipline = database.session.query(Discipline).filter(Discipline.discipline_code == "Discipline_1").first()

    return ScrapeConfig(
        year=2023,
        category=BestlistCategory.ALL_MEN,
        discipline=discipline,
        allow_wind=True,
        amount=10,
        only_homologated=False,
    )


def get_sample_synchronizer() -> BestlistSynchronizer:
    sample_bestlist = pd.read_csv(DF_PATH, keep_default_na=False, dtype=str)
    config = get_minimal_config()
    scrape_config = get_scrape_config()
    return BestlistSynchronizer(config, scrape_config, sample_bestlist)


def test_init():
    sample_bestlist = pd.read_csv(DF_PATH, keep_default_na=False, dtype=str)
    config = get_minimal_config()
    scrape_config = get_scrape_config()
    synchronizer = BestlistSynchronizer(config, scrape_config, sample_bestlist)

    assert synchronizer.config == config
    assert synchronizer.scrape_config == scrape_config
    assert "Nr" not in synchronizer.original_bestlist.columns
    assert synchronizer.bl_limit_reached


# pylint: disable=too-many-statements
def test__fetch_records_from_database():
    with DatabaseConnection(get_minimal_config()) as database:
        result = Result(
            athlete_id=1,
            club_id=1,
            event_id=1,
            discipline_id=1,
            performance=833,
            wind=None,
            rank="1f1",
            location="Thun",
            date=date.fromisoformat("2023-10-10"),
            points=0,
            homologated=True,
            manual=False,
        )
        database.session.add(result)
        database.session.commit()

        sample_bestlist = pd.read_csv(DF_PATH, keep_default_na=False, dtype=str)
        config = get_minimal_config()
        scrape_config = get_scrape_config()
        synchronizer = BestlistSynchronizer(config, scrape_config, sample_bestlist)

        db_records = synchronizer._fetch_records_from_database(scrape_config.discipline, 832)

        assert len(db_records) == 1
        record = db_records[0]

        assert record.id == 1
        assert record.performance == 833
        assert record.wind is None
        assert not record.not_homologated
        assert not record.manual
        assert record.athlete == "Max Mustermann"
        assert record.club == "LV Muster"
        assert record.nationality == "SUI"
        assert record.birthdate == date.fromisoformat("2000-02-15")
        assert record.event == "Test Event"
        assert record.location == "Thun"
        assert record.event_date == date.fromisoformat("2023-10-10")
        assert record.athlete_code == "Athlete_1"
        assert record.club_code == "Club_1"
        assert record.event_code == "Event_1"

        result.performance = 830
        database.session.commit()
        assert len(synchronizer._fetch_records_from_database(scrape_config.discipline, 832)) == 0
        result.performance = 833

        result.date = date.fromisoformat("2022-11-10")
        database.session.commit()
        assert len(synchronizer._fetch_records_from_database(scrape_config.discipline, 832)) == 0
        result.date = date.fromisoformat("2023-10-10")

        result.discipline_id = 2
        database.session.commit()
        assert len(synchronizer._fetch_records_from_database(scrape_config.discipline, 832)) == 0
        result.discipline_id = 1

        scrape_config.allow_wind = False
        result.wind = 2.1
        database.session.commit()
        assert len(synchronizer._fetch_records_from_database(scrape_config.discipline, 832)) == 0
        scrape_config.allow_wind = True
        result.wind = None

        scrape_config.only_homologated = True
        result.homologated = False
        database.session.commit()
        assert len(synchronizer._fetch_records_from_database(scrape_config.discipline, 832)) == 0
        scrape_config.only_homologated = False
        result.homologated = True

        database.session.commit()

        result2 = Result(
            athlete_id=1,
            club_id=1,
            rank="",
            event_id=1,
            discipline_id=1,
            performance=835,
            wind=None,
            location="Zürich",
            date=date.fromisoformat("2023-05-10"),
            points=0,
        )
        database.session.add(result2)
        database.session.commit()

        records = synchronizer._fetch_records_from_database(scrape_config.discipline, 832)
        assert len(records) == 2

        assert records[0].id == 2
        assert records[1].id == 1

        database.session.delete(result)
        database.session.delete(result2)
        database.session.commit()


def test__update_entries():
    athlete = Athlete(
        athlete_code="Athlete_1",
        name="Max Mustermann",
        birthdate=date.fromisoformat("2000-02-15"),
        nationality="SUI",
        latest_date=date.fromisoformat("2023-01-11"),
    )
    club = Club(club_code="Club_1", name="LV Muster", latest_date=date.fromisoformat("2023-01-11"))
    event = Event(event_code="Event_1", name="Test Event", latest_date=date.fromisoformat("2023-01-11"))

    record = Record(
        performance=833,
        wind=-2.0,
        rank="1f1",
        not_homologated=False,
        athlete="Max Mustermann",
        club="LV Muster",
        nationality="SUI",
        birthdate=date.fromisoformat("2000-02-15"),
        event="Test Event",
        location="Thun",
        event_date=date.fromisoformat("2023-01-11"),
        athlete_code="Athlete_1",
        club_code="Club_1",
        event_code="Event_1",
    )

    assert BestlistSynchronizer._update_entries(athlete, club, event, record) == 0

    record.athlete = "Max"
    record.event_date = date(2023, 1, 10)
    assert BestlistSynchronizer._update_entries(athlete, club, event, record) == 0
    assert athlete.latest_date == date.fromisoformat("2023-01-11")
    assert athlete.name == "Max Mustermann"

    record.event_date = date(2023, 2, 11)
    assert BestlistSynchronizer._update_entries(athlete, club, event, record) == 1
    assert athlete.name == "Max"
    assert athlete.latest_date == date(2023, 2, 11)
    assert club.latest_date == date(2023, 2, 11)
    assert event.latest_date == date(2023, 2, 11)

    record.birthdate = date(2000, 3, 15)
    record.event = "Event"
    record.club = "LV Tester"
    assert BestlistSynchronizer._update_entries(athlete, club, event, record) == 3


# pylint: disable=too-many-statements
def test__compare_records():
    synchronizer = get_sample_synchronizer()
    synchronizer.bl_limit_reached = False

    bl_records = RecordCollection(
        records=[
            get_sample_record(833),
            get_sample_record(820),
            get_sample_record(800),
        ]
    )

    db_records = RecordCollection(
        records=[
            get_sample_record(833),
            get_sample_record(820),
            get_sample_record(800),
        ]
    )

    empty_records = RecordCollection(records=[])

    # check if records from bl and db are equal
    insertion_mask, deletion_mask, similarities = synchronizer._compare_records(bl_records, db_records, False)
    assert insertion_mask == [False, False, False]
    assert deletion_mask == [False, False, False]
    assert len(similarities) == 0

    # check if we have one duplicate
    bl_records[1].performance = 833
    insertion_mask, deletion_mask, similarities = synchronizer._compare_records(bl_records, empty_records, False)
    assert insertion_mask == [True, False, True]
    assert len(deletion_mask) == 0
    assert len(similarities) == 0
    bl_records[1].performance = 820

    # check if we have result-unrelated differences
    bl_records[0].athlete = "Max"
    bl_records[2].club = "LV Mustermann"
    insertion_mask, deletion_mask, similarities = synchronizer._compare_records(bl_records, db_records, False)
    assert (0, 0) in similarities and (2, 2) in similarities and len(similarities) == 2
    assert insertion_mask == [True, False, True]
    assert deletion_mask == [True, False, True]
    bl_records[0].athlete = "Max Mustermann"
    bl_records[2].club = "LV Muster"

    # check if we have result-related differences
    bl_records[1].wind = 1.2
    bl_records[2].location = "Zürich"
    insertion_mask, deletion_mask, similarities = synchronizer._compare_records(bl_records, db_records, False)
    assert insertion_mask == [False, True, True]
    assert deletion_mask == [False, True, True]
    assert len(similarities) == 0
    bl_records[1].wind = -2.0
    bl_records[2].location = "Thun"

    # check if we have different order of records
    bl_records[1].performance = 833
    bl_records[1].event_date = date.fromisoformat("2023-02-11")
    db_records[0].event_date = date.fromisoformat("2023-02-11")
    db_records[1].performance = 833
    insertion_mask, deletion_mask, similarities = synchronizer._compare_records(bl_records, db_records, False)
    assert insertion_mask == [False, False, False]
    assert deletion_mask == [False, False, False]
    assert len(similarities) == 0
    bl_records[1].performance = 820
    bl_records[1].event_date = date.fromisoformat("2023-01-11")
    db_records[0].event_date = date.fromisoformat("2023-01-11")
    db_records[1].performance = 820

    # check whether out of bestlist bounds are kept
    synchronizer.bl_limit_reached = True
    bl_records[2].club = "LV Mustermann"
    insertion_mask, deletion_mask, similarities = synchronizer._compare_records(bl_records, db_records, False)
    assert (2, 2) in similarities and len(similarities) == 1
    assert insertion_mask == [False, False, True]
    assert deletion_mask == [False, False, False]
    bl_records[2].club = "LV Muster"


def get_sample_record(performance: int) -> Record:
    return Record(
        performance=performance,
        wind=-2.0,
        rank="1f1",
        not_homologated=False,
        athlete="Max Mustermann",
        club="LV Muster",
        nationality="SUI",
        birthdate=date.fromisoformat("2000-02-15"),
        event="Test Event",
        location="Thun",
        event_date=date.fromisoformat("2023-01-11"),
        athlete_code="Athlete_1",
        club_code="Club_1",
        event_code="Event_1",
    )


def test__insert_records():
    synchronizer = get_sample_synchronizer()

    record1 = get_sample_record(833)

    record2 = get_sample_record(820)
    record2.athlete = "Petra Tester"
    record2.nationality = "GER"
    record2.event = "Test Event 2"
    record2.club = "LV Thun"
    record2.event_date = date.fromisoformat("2023-02-11")
    record2.athlete_code = "Athlete_2"
    record2.event_code = "Event_2"

    with DatabaseConnection(get_minimal_config()) as database:
        sync_statistics = synchronizer._insert_records(
            database.session,
            [record1, record2],
            1,
            BestlistCategory.get_age_bounds(synchronizer.scrape_config.category),
        )
        database.session.commit()
        assert sync_statistics.added_records == 2
        assert sync_statistics.added_athletes == 1  # Petra Tester
        assert sync_statistics.added_clubs == 0
        assert sync_statistics.added_events == 1  # Test Event 2
        assert sync_statistics.updates == 1  # LV Muster -> LV Thun

        results: list[Result] = database.session.query(Result).order_by(Result.performance.desc()).all()
        assert len(results) == 2
        assert results[0].performance == 833 and results[0].athlete.name == "Max Mustermann"
        assert results[1].performance == 820 and results[1].athlete.name == "Petra Tester"

        athlete2: Athlete = database.session.query(Athlete).filter(Athlete.athlete_code == "Athlete_2").first()
        assert athlete2.name == "Petra Tester"
        assert athlete2.birthdate == date(2000, 2, 15)
        assert athlete2.nationality == "GER"
        assert athlete2.latest_date == date(2023, 2, 11)

        club: Club = database.session.query(Club).filter(Club.club_code == "Club_1").first()
        assert club.name == "LV Thun"
        assert club.latest_date == date(2023, 2, 11)

        event2: Event = database.session.query(Event).filter(Event.event_code == "Event_2").first()
        assert event2.name == "Test Event 2"

        database.session.delete(results[0])
        database.session.delete(results[1])
        database.session.delete(athlete2)
        database.session.delete(event2)
        database.session.commit()


def test_synchronize():
    synchronizer = get_sample_synchronizer()
    with DatabaseConnection(get_minimal_config()) as database:
        result = Result(
            athlete_id=1,
            club_id=1,
            event_id=1,
            discipline_id=1,
            performance=832,
            wind=0.0,
            rank="1f1",
            location="Loc1",
            date=date.fromisoformat("2022-10-10"),
            points=0,
        )
        database.session.add(result)
        database.session.commit()

    ignored_entries = {
        '{"Resultat":"8.12a","Wind":"0.0","Rang":"1f1","Name":"Tester_5","Verein":"Club_5",'
        '"Nat.":"SUI","Geb. Dat.":"05.05.1998","Wettkampf":"Event_5","Ort":"Loc5","Datum":"05.08.2022",'
        '"athlete_code":"CONTACT.WEB.131887","club_code":"ACC_1.SGALV.1011",'
        '"event_code":"a21aa-pjr8yn-leb1bjdk-1-lemufw3n-lw9"}',
        '{"Resultat":"8.03","Wind":"1.4","Rang":"1f1","Name":"Tester_7","Verein":"Club_7",'
        '"Nat.":"SUI","Geb. Dat.":"07.13.1998","Wettkampf":"Event_7","Ort":"Loc7","Datum":"07.08.2022",'
        '"athlete_code":"CONTACT.WEB.131887","club_code":"ACC_1.SGALV.1011",'
        '"event_code":"a21aa-oz1dk-lia60e1y-1-liihyltl-ilg3"}',
    }
    with tempfile.NamedTemporaryFile() as error_file:
        path = pathlib.Path(error_file.name)
        sync_statistics = synchronizer.synchronize(path, ignored_entries)

        assert sync_statistics.added_records == 7
        assert sync_statistics.added_athletes == 1
        assert sync_statistics.added_clubs == 1
        assert sync_statistics.added_events == 6

        lines = error_file.readlines()
        assert len(lines) == 1
        assert lines[0].decode().startswith('{"Resultat":"8.19"')

        results: [Result] = database.session.query(Result).order_by(Result.performance.desc(), Result.date.asc()).all()
        assert len(results) == 8
        assert results[0].athlete.name == "Max"
        assert results[0].performance == 832

        athletes: [Athlete] = database.session.query(Athlete).order_by(Athlete.athlete_code.asc()).all()
        assert len(athletes) == 2
        assert athletes[0].athlete_code == "Athlete_1"
        assert athletes[1].name == "Tester_10"
        assert athletes[1].latest_date == date(2022, 8, 10)

        assert database.session.query(Club).count() == 2
        assert database.session.query(Event).count() == 7
