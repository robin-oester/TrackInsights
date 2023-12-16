import os
import pathlib
import tempfile
from datetime import date

import pandas as pd
import numpy as np

from track_insights.database import DatabaseConnection
from track_insights.database.models import Athlete, Club, DisciplineConfiguration, Discipline, Event, Result
from track_insights.scraping import ScrapeConfig, Processor, BestlistField

DATABASE = pathlib.Path(os.path.abspath(__file__)).parent / "test_processor.database"
DF_PATH = pathlib.Path(os.path.abspath(__file__)).parent / "resources" / "sample_dataframe.csv"


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


def setup():
    DATABASE.unlink(True)

    with DatabaseConnection(get_minimal_config()) as database:
        database.create_tables()

        athlete = Athlete(
            athlete_code="Athlete_1",
            name="Max Mustermann",
            birthdate=date.fromisoformat("2000-02-15"),
            nationality="SUI",
            latest_date=date.fromisoformat("2023-01-11")
        )

        club = Club(
            club_code="Club_1",
            name="LV Muster",
            latest_date=date.fromisoformat("2023-01-11")
        )

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

        event = Event(
            event_code="Event_1",
            name="Test Event",
            latest_date=date.fromisoformat("2023-01-11")
        )

        database.session.add(athlete)
        database.session.add(club)
        database.session.add(discipline_config)
        database.session.add(discipline)
        database.session.add(event)
        database.session.commit()


def teardown():
    DATABASE.unlink()


def get_scrape_config() -> ScrapeConfig:
    return ScrapeConfig(
        year=2023,
        category='M',
        male=True,
        discipline_code="Discipline_1",
        indoor=False,
        allow_wind=True,
        amount=30,
        allow_nonhomologated=True
    )


def get_sample_processor() -> Processor:
    ignored_entries = {
        '{"Resultat":"8.12a","Wind":"0.0","Rang":"1f1","Name":"Tester_5","Verein":"Club_5","Nat.":"SUI","Geb. Dat.":"05.05.1998","Wettkampf":"Event_5","Ort":"Loc5","Datum":"05.08.2022","athlete_code":"CONTACT.WEB.131887","club_code":"ACC_1.SGALV.1011","event_code":"a21aa-pjr8yn-leb1bjdk-1-lemufw3n-lw9"}',
        '{"Resultat":"8.03","Wind":"1.4","Rang":"1f1","Name":"Tester_7","Verein":"Club_7","Nat.":"SUI","Geb. Dat.":"07.13.1998","Wettkampf":"Event_7","Ort":"Loc7","Datum":"07.08.2022","athlete_code":"CONTACT.WEB.131887","club_code":"ACC_1.SGALV.1011","event_code":"a21aa-oz1dk-lia60e1y-1-liihyltl-ilg3"}'
    }
    sample_bestlist = pd.read_csv(DF_PATH, keep_default_na=False, dtype=str)
    config = get_minimal_config()
    scrape_config = get_scrape_config()
    return Processor(config, scrape_config, sample_bestlist, ignored_entries)


def test_init():
    ignored_entries = {
        '{"Resultat":"8.12","Wind":"0.0","Rang":"1f1","Name":"Tester_5","Verein":"Club_5","Nat.":"SUI","Geb. Dat.":"05.05.1998","Wettkampf":"Event_5","Ort":"Loc5","Datum":"05.08.2022","athlete_code":"CONTACT.WEB.131887","club_code":"ACC_1.SGALV.1011","event_code":"a21aa-pjr8yn-leb1bjdk-1-lemufw3n-lw9"}',
        '{"Resultat":"8.03","Wind":"1.4","Rang":"1f1","Name":"Tester_7","Verein":"Club_7","Nat.":"SUI","Geb. Dat.":"07.05.1998","Wettkampf":"Event_7","Ort":"Loc7","Datum":"07.08.2022","athlete_code":"CONTACT.WEB.131887","club_code":"ACC_1.SGALV.1011","event_code":"a21aa-oz1dk-lia60e1y-1-liihyltl-ilg3"}'
    }
    sample_bestlist = pd.read_csv(DF_PATH, keep_default_na=False, dtype=str)
    config = get_minimal_config()
    scrape_config = get_scrape_config()
    processor = Processor(config, scrape_config, sample_bestlist, ignored_entries)

    assert processor.config == config
    assert processor.scrape_config == scrape_config
    assert processor.ignored_entries == ignored_entries
    assert "Nr" not in processor.original_bestlist.columns
    assert not processor.homologation_relevant
    assert processor.wind_relevant


def test__parse_result():
    assert Processor._parse_result("6.21") == 621
    assert Processor._parse_result("8") == 800
    assert Processor._parse_result("15.93") == 1593
    assert Processor._parse_result("27.3") == 2730
    assert Processor._parse_result("63.81") == 6381
    assert Processor._parse_result("82.99") == 8299
    assert Processor._parse_result("102.1") == 10210
    assert Processor._parse_result("5103") == 510300
    assert Processor._parse_result("10931") == 1093100

    assert Processor._parse_result("0:09.14") == 914
    assert Processor._parse_result("0:45.4") == 4540
    assert Processor._parse_result("0:59.64") == 5964
    assert Processor._parse_result("1:00.23") == 6023
    assert Processor._parse_result("01:35.5") == 9550
    assert Processor._parse_result("2:04.39") == 12439
    assert Processor._parse_result("12:49.48") == 76948
    assert Processor._parse_result("27:36.2") == 165620
    assert Processor._parse_result("63:12.3") == 379230

    assert Processor._parse_result("1:05:15.10") == 391510
    assert Processor._parse_result("01:28:49.6") == 532960
    assert Processor._parse_result("25:58:32") == 9351200

    assert Processor._parse_result("10.23_SR_U23") == 1023
    assert Processor._parse_result("1:02.48_SB\nWind") == 6248

    assert Processor._parse_result("12,4") == -1
    assert Processor._parse_result("1:62.9") == -1
    assert Processor._parse_result("83.48.12") == -1
    assert Processor._parse_result("25:12:54:31") == -1
    assert Processor._parse_result("10.a4") == -1


def test__results_to_records():
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
            date=date.fromisoformat("2022-10-10"),
            points=0
        )
        database.session.add(result)
        database.session.commit()

        records = Processor._results_to_records([result])

        assert len(records) == 1
        record = records[0]

        assert record[BestlistField.ID.value] == 1
        assert record[BestlistField.RESULT.value] == 833
        assert np.isnan(record[BestlistField.WIND.value])
        assert not record[BestlistField.NOT_HOMOLOGATED.value]
        assert record[BestlistField.ATHLETE.value] == "Max Mustermann"
        assert record[BestlistField.CLUB.value] == "LV Muster"
        assert record[BestlistField.NATIONALITY.value] == "SUI"
        assert record[BestlistField.BIRTHDATE.value] == date.fromisoformat("2000-02-15")
        assert record[BestlistField.EVENT.value] == "Test Event"
        assert record[BestlistField.LOCATION.value] == "Thun"
        assert record[BestlistField.DATE.value] == date.fromisoformat("2022-10-10")
        assert record[BestlistField.ATHLETE_CODE.value] == "Athlete_1"
        assert record[BestlistField.CLUB_CODE.value] == "Club_1"
        assert record[BestlistField.EVENT_CODE.value] == "Event_1"

        database.session.delete(result)
        database.session.commit()


def test__read_results_from_database():
    with DatabaseConnection(get_minimal_config()) as database:
        result = Result(
            athlete_id=1,
            club_id=1,
            event_id=1,
            discipline_id=1,
            performance=833,
            location="Zürich",
            date=date.fromisoformat("2023-11-10"),
            points=0
        )

        database.session.add(result)
        database.session.commit()

        discipline = database.session.get(Discipline, 1)

        processor = get_sample_processor()
        assert len(processor._read_results_from_database(discipline)) == 1

        result.manual = True
        database.session.commit()
        assert len(processor._read_results_from_database(discipline)) == 0

        result.manual = False
        result.date = date.fromisoformat("2022-11-10")
        database.session.commit()
        assert len(processor._read_results_from_database(discipline)) == 0

        result.date = date.fromisoformat("2023-11-10")
        result.discipline_id = 2
        database.session.commit()
        assert len(processor._read_results_from_database(discipline)) == 0

        result.discipline_id = 1
        processor.scrape_config.allow_wind = False
        result.wind = 2.1
        database.session.commit()
        assert len(processor._read_results_from_database(discipline)) == 0

        processor.scrape_config.allow_nonhomologated = False
        processor.scrape_config.allow_wind = True
        result.homologated = False
        database.session.commit()
        assert len(processor._read_results_from_database(discipline)) == 0

        processor.scrape_config.allow_nonhomologated = True
        result.homologated = True
        result2 = Result(
            athlete_id=1,
            club_id=1,
            event_id=1,
            discipline_id=1,
            performance=835,
            location="Zürich",
            date=date.fromisoformat("2023-05-10"),
            points=0
        )
        database.session.add(result2)
        database.session.commit()

        found_results = processor._read_results_from_database(discipline)
        assert len(found_results) == 2
        assert found_results[0][BestlistField.ID.value] == 2
        assert found_results[1][BestlistField.ID.value] == 1

        database.session.delete(result)
        database.session.delete(result2)
        database.session.commit()


def test__sanity_check_results():
    df_1 = pd.DataFrame(data=[100, 101], columns=[BestlistField.RESULT.value])
    assert Processor._sanity_check_results(df_1, True)
    assert not Processor._sanity_check_results(df_1, False)

    df_1 = pd.DataFrame(data=[542, 332, 332, 18], columns=[BestlistField.RESULT.value])
    assert Processor._sanity_check_results(df_1, False)
    assert not Processor._sanity_check_results(df_1, True)

    df_1 = pd.DataFrame(data=[123, 543, 324, 34], columns=[BestlistField.RESULT.value])
    assert not Processor._sanity_check_results(df_1, False)
    assert not Processor._sanity_check_results(df_1, True)


def test__compare_record_fields():
    dtypes = np.dtype(
        [
            BestlistField.ID.get_dtype_pair(),
            BestlistField.WIND.get_dtype_pair(),
            BestlistField.RANK.get_dtype_pair(),
            BestlistField.NOT_HOMOLOGATED.get_dtype_pair(),
            BestlistField.DATE.get_dtype_pair(),
        ]
    )

    data = np.array([(10, -1.2, "1f1", False, np.datetime64("2023-09-10")),
                     (10, 5, "1f1", True, np.datetime64("2023-09-10")),
                     (101, 5, "1f1", False, np.datetime64("2023-10-10"))], dtype=dtypes)

    records = data.view(np.recarray)

    assert Processor._compare_record_fields(records[0], records[0], [
        BestlistField.ID,
        BestlistField.WIND,
        BestlistField.RANK,
        BestlistField.NOT_HOMOLOGATED,
        BestlistField.DATE
    ])

    assert Processor._compare_record_fields(records[0], records[1], [
        BestlistField.ID,
        BestlistField.RANK,
        BestlistField.DATE
    ])

    assert not Processor._compare_record_fields(records[0], records[1], [
        BestlistField.ID,
        BestlistField.WIND,
        BestlistField.RANK
    ])

    assert Processor._compare_record_fields(records[1], records[2], [
        BestlistField.WIND,
        BestlistField.RANK
    ])

    assert not Processor._compare_record_fields(records[1], records[2], [
        BestlistField.WIND,
        BestlistField.RANK,
        BestlistField.DATE
    ])


def test__update_entries():
    athlete = Athlete(
        athlete_code="Athlete_1",
        name="Max Mustermann",
        birthdate=date.fromisoformat("2000-02-15"),
        nationality="SUI",
        latest_date=date.fromisoformat("2023-01-11")
    )
    club = Club(
        club_code="Club_1",
        name="LV Muster",
        latest_date=date.fromisoformat("2023-01-11")
    )
    event = Event(
        event_code="Event_1",
        name="Test Event",
        latest_date=date.fromisoformat("2023-01-11")
    )

    record = np.record((1, -2.0, "1f1", False, "Max Mustermann", "LV Muster", "SUI", np.datetime64("2000-02-15"),
                        "Test Event", "Thun", np.datetime64("2023-01-11"), "Athlete_1",
                        "Club_1", "Event_1"), dtype=get_sample_bestlist_record_type())
    assert Processor._update_entries(athlete, club, event, record) == 0

    record[BestlistField.ATHLETE.value] = "Max"
    record[BestlistField.DATE.value] = date(2023, 1, 10)
    assert Processor._update_entries(athlete, club, event, record) == 0
    assert athlete.latest_date == np.datetime64("2023-01-11")
    assert athlete.name == "Max Mustermann"

    record[BestlistField.DATE.value] = date(2023, 2, 11)
    assert Processor._update_entries(athlete, club, event, record) == 1
    assert athlete.name == "Max"
    assert athlete.latest_date == date(2023, 2, 11)
    assert club.latest_date == date(2023, 2, 11)
    assert event.latest_date == date(2023, 2, 11)

    record[BestlistField.BIRTHDATE.value] = date(2000, 3, 15)
    record[BestlistField.EVENT.value] = "Event"
    record[BestlistField.CLUB.value] = "LV Tester"
    assert Processor._update_entries(athlete, club, event, record) == 3


def get_sample_bestlist_record_type() -> np.dtype:
    return np.dtype(
        [
            BestlistField.RESULT.get_dtype_pair(),
            BestlistField.WIND.get_dtype_pair(),
            BestlistField.RANK.get_dtype_pair(),
            BestlistField.NOT_HOMOLOGATED.get_dtype_pair(),
            BestlistField.ATHLETE.get_dtype_pair(),
            BestlistField.CLUB.get_dtype_pair(),
            BestlistField.NATIONALITY.get_dtype_pair(),
            BestlistField.BIRTHDATE.get_dtype_pair(),
            BestlistField.EVENT.get_dtype_pair(),
            BestlistField.LOCATION.get_dtype_pair(),
            BestlistField.DATE.get_dtype_pair(),
            BestlistField.ATHLETE_CODE.get_dtype_pair(),
            BestlistField.CLUB_CODE.get_dtype_pair(),
            BestlistField.EVENT_CODE.get_dtype_pair(),
        ]
    )


def test__get_record_similarity():
    processor = get_sample_processor()

    record1 = np.record((1, -2.0, "1f1", False, "Max Mustermann", "LV Muster", "SUI", np.datetime64("2000-02-15"),
                         "Test Event", "Thun", np.datetime64("2023-01-11"), "Athlete_1",
                         "Club_1", "Event_1"), dtype=get_sample_bestlist_record_type())
    record2 = np.record((1, -2.0, "1f1", False, "Max Mustermann", "LV Muster", "SUI", np.datetime64("2000-02-15"),
                         "Test Event", "Thun", np.datetime64("2023-01-11"), "Athlete_1",
                         "Club_1", "Event_1"), dtype=get_sample_bestlist_record_type())

    record2[BestlistField.WIND.value] = -2.01
    assert processor._get_record_similarity(record1, record2) == 1

    record2[BestlistField.WIND.value] = 1
    assert processor._get_record_similarity(record1, record2) == -1

    record2[BestlistField.WIND.value] = record1[BestlistField.WIND.value]
    record2[BestlistField.DATE.value] = date(2023, 2, 11)
    record2[BestlistField.ATHLETE.value] = "Max"
    assert processor._get_record_similarity(record1, record2) == -1

    record2[BestlistField.DATE.value] = record1[BestlistField.DATE.value]
    assert processor._get_record_similarity(record1, record2) == 0

    record2[BestlistField.ATHLETE.value] = record1[BestlistField.ATHLETE.value]
    record2[BestlistField.EVENT.value] = "Event_2"
    assert processor._get_record_similarity(record1, record2) == 0

    record2[BestlistField.EVENT.value] = record1[BestlistField.EVENT.value]
    record2[BestlistField.CLUB.value] = "Club_"
    assert processor._get_record_similarity(record1, record2) == 0


def test__compare_records():
    processor = get_sample_processor()

    bl_records = np.array([
        (833, -2.0, "1f1", False, "Max Mustermann", "LV Muster", "SUI", np.datetime64("2000-02-15"),
         "Test Event", "Thun", np.datetime64("2023-01-11"), "Athlete_1",
         "Club_1", "Event_1"),
        (820, -2.0, "1f1", False, "Max Mustermann", "LV Muster", "SUI", np.datetime64("2000-02-15"),
         "Test Event", "Thun", np.datetime64("2023-01-11"), "Athlete_1",
         "Club_1", "Event_1"),
        (800, -2.0, "1f1", False, "Max Mustermann", "LV Muster", "SUI", np.datetime64("2000-02-15"),
         "Test Event", "Thun", np.datetime64("2023-01-11"), "Athlete_1",
         "Club_1", "Event_1")
    ], dtype=get_sample_bestlist_record_type()).view(np.recarray)

    db_records = np.array([
        (833, -2.0, "1f1", False, "Max Mustermann", "LV Muster", "SUI", np.datetime64("2000-02-15"),
         "Test Event", "Thun", np.datetime64("2023-01-11"), "Athlete_1",
         "Club_1", "Event_1"),
        (820, -2.0, "1f1", False, "Max Mustermann", "LV Muster", "SUI", np.datetime64("2000-02-15"),
         "Test Event", "Thun", np.datetime64("2023-01-11"), "Athlete_1",
         "Club_1", "Event_1"),
        (800, -2.0, "1f1", False, "Max Mustermann", "LV Muster", "SUI", np.datetime64("2000-02-15"),
         "Test Event", "Thun", np.datetime64("2023-01-11"), "Athlete_1",
         "Club_1", "Event_1")
    ], dtype=get_sample_bestlist_record_type()).view(np.recarray)

    empty_records = np.array([], dtype=get_sample_bestlist_record_type()).view(np.recarray)

    # check if records from bl and db are equal
    insertion_mask, deletion_mask, similarities = processor._compare_records(bl_records, db_records, False)
    assert (~insertion_mask).all()
    assert (~deletion_mask).all()
    assert len(similarities) == 0

    # check if we have one duplicate
    bl_records[1][BestlistField.RESULT.value] = 833
    insertion_mask, deletion_mask, similarities = processor._compare_records(bl_records, empty_records, False)
    assert (insertion_mask == [True, False, True]).all()
    assert len(deletion_mask) == 0
    assert len(similarities) == 0
    bl_records[1][BestlistField.RESULT.value] = 820

    # check if we have result-unrelated differences
    bl_records[0][BestlistField.ATHLETE.value] = "Max"
    bl_records[2][BestlistField.CLUB.value] = "LV Mustermann"
    insertion_mask, deletion_mask, similarities = processor._compare_records(bl_records, db_records, False)
    assert (insertion_mask == [True, False, True]).all()
    assert (deletion_mask == [True, False, True]).all()
    assert (0, 0) in similarities and (2, 2) in similarities and len(similarities) == 2
    bl_records[0][BestlistField.ATHLETE.value] = "Max Mustermann"
    bl_records[2][BestlistField.CLUB.value] = "LV Muster"

    # check if we have result-related differences
    bl_records[1][BestlistField.WIND.value] = 1.2
    bl_records[2][BestlistField.LOCATION.value] = "Zürich"
    insertion_mask, deletion_mask, similarities = processor._compare_records(bl_records, db_records, False)
    assert (insertion_mask == [False, True, True]).all()
    assert (deletion_mask == [False, True, True]).all()
    assert len(similarities) == 0
    bl_records[1][BestlistField.WIND.value] = -2.0
    bl_records[2][BestlistField.LOCATION.value] = "Thun"

    # check if we have different order of records
    bl_records[1][BestlistField.RESULT.value] = 833
    bl_records[1][BestlistField.DATE.value] = np.datetime64("2023-02-11")
    db_records[1][BestlistField.RESULT.value] = 833
    db_records[0][BestlistField.DATE.value] = np.datetime64("2023-02-11")
    insertion_mask, deletion_mask, similarities = processor._compare_records(bl_records, db_records, False)
    assert (~insertion_mask).all()
    assert (~deletion_mask).all()
    assert len(similarities) == 0


def test__insert_records():
    processor = get_sample_processor()
    records = np.array([
        (833, -2.0, "1f1", False, "Max Mustermann", "LV Muster", "SUI", np.datetime64("2000-02-15"),
         "Test Event", "Thun", np.datetime64("2023-01-11"), "Athlete_1",
         "Club_1", "Event_1"),
        (820, -2.0, "1f1", False, "Petra Tester", "LV Thun", "GER", np.datetime64("2000-02-15"),
         "Test Event 2", "Thun", np.datetime64("2023-02-11"), "Athlete_2",
         "Club_1", "Event_2")
    ], dtype=get_sample_bestlist_record_type()).view(np.recarray)

    with DatabaseConnection(get_minimal_config()) as database:
        (added_athletes, added_clubs, added_events), amount_updates = processor._insert_records(database.session, records, 1)
        database.session.commit()
        assert added_athletes == 1  # Petra Tester
        assert added_clubs == 0
        assert added_events == 1  # Test Event 2
        assert amount_updates == 1  # LV Muster -> LV Thun

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


def test_process():
    processer = get_sample_processor()
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
            points=0
        )
        database.session.add(result)
        database.session.commit()

    with tempfile.NamedTemporaryFile() as error_file:
        path = pathlib.Path(error_file.name)
        processer.process(path)

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
