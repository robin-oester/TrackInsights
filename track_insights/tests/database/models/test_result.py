# pylint: disable=redefined-outer-name
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from track_insights.database.models import (
    Athlete,
    Club,
    Discipline,
    DisciplineConfiguration,
    DisciplineType,
    Event,
    Result,
)


@pytest.fixture(autouse=True)
def session():
    engine = create_engine("sqlite:///:memory:", echo=True)
    sess = sessionmaker(bind=engine)()

    Athlete.metadata.create_all(engine)
    Club.metadata.create_all(engine)
    DisciplineConfiguration.metadata.create_all(engine)
    Discipline.metadata.create_all(engine)
    Event.metadata.create_all(engine)

    athlete = Athlete(
        athlete_code="Athlete_123",
        name="Max Mustermann",
        birthdate=date.fromisoformat("2000-02-15"),
        nationality="SUI",
        latest_date=date.fromisoformat("2023-10-10"),
    )
    club = Club(club_code="Club_123", name="LV Muster", latest_date=date.fromisoformat("2023-10-10"))
    event = Event(event_code="Event_123", name="Test Event", latest_date=date.fromisoformat("2023-10-10"))
    discipline_config = DisciplineConfiguration(name="Weit", discipline_type=DisciplineType.JUMP)
    discipline = Discipline(
        discipline_code="Discipline_123",
        config=discipline_config,
        indoor=False,
        male=True,
    )
    sess.add(athlete)
    sess.add(club)
    sess.add(event)
    sess.add(discipline_config)
    sess.add(discipline)

    yield sess

    sess.close()
    engine.dispose()


def test_add_result(session):
    result = Result(
        athlete_id=1,
        club_id=1,
        event_id=1,
        discipline_id=1,
        performance=1000,
        wind=1.4,
        rank="1f1",
        location="Bern",
        date=date.fromisoformat("2023-10-10"),
        homologated=True,
    )
    session.add(result)
    session.commit()

    extracted_result: Result = session.query(Result).filter(Result.id == 1).first()

    assert extracted_result is not None
    assert extracted_result.performance == 1000
    assert float(extracted_result.wind) == 1.4
    assert extracted_result.rank == "1f1"
    assert extracted_result.location == "Bern"
    assert extracted_result.date == date.fromisoformat("2023-10-10")
    assert extracted_result.homologated
    assert not extracted_result.ignore
    assert not extracted_result.manual

    assert extracted_result.athlete.athlete_code == "Athlete_123"
    assert extracted_result.athlete.name == "Max Mustermann"
    assert extracted_result.athlete.birthdate == date.fromisoformat("2000-02-15")
    assert extracted_result.athlete.nationality == "SUI"
    assert extracted_result.athlete.latest_date == extracted_result.date

    extracted_results: [Result] = session.query(Athlete).filter(Athlete.id == 1).first().results
    assert len(extracted_results) == 1
    assert extracted_results[0].performance == 1000

    assert extracted_result.club.club_code == "Club_123"
    assert extracted_result.club.name == "LV Muster"
    assert extracted_result.club.latest_date == date.fromisoformat("2023-10-10")

    extracted_results = session.query(Club).filter(Club.id == 1).first().results
    assert len(extracted_results) == 1
    assert extracted_results[0].rank == "1f1"

    assert extracted_result.event.event_code == "Event_123"
    assert extracted_result.event.name == "Test Event"
    assert extracted_result.event.latest_date == date.fromisoformat("2023-10-10")

    extracted_results = session.query(Event).filter(Event.id == 1).first().results
    assert len(extracted_results) == 1
    assert extracted_results[0].location == "Bern"

    assert extracted_result.discipline.config.name == "Weit"
    assert not extracted_result.discipline.config.is_ascending()
    assert extracted_result.discipline.discipline_code == "Discipline_123"
    assert not extracted_result.discipline.indoor
    assert extracted_result.discipline.male

    extracted_results = session.query(Discipline).filter(Discipline.id == 1).first().results
    assert len(extracted_results) == 1
    assert extracted_results[0].date == date.fromisoformat("2023-10-10")


def test_update_result(session):
    result = Result(
        athlete_id=1,
        club_id=1,
        event_id=1,
        discipline_id=1,
        performance=1000,
        wind=1.4,
        rank="1f1",
        location="Bern",
        date=date.fromisoformat("2023-10-10"),
        homologated=True,
    )
    session.add(result)
    session.commit()

    athlete = Athlete(
        athlete_code="Athlete_321",
        name="Petra Tester",
        birthdate=date.fromisoformat("2002-02-20"),
        nationality="GER",
        latest_date=date.fromisoformat("2023-10-10"),
    )
    session.add(athlete)

    result.athlete = athlete
    result.wind = 2.1
    result.location = "Zürich"
    session.commit()

    extracted_result: Result = session.query(Result).filter(Result.id == 1).first()
    assert extracted_result.athlete.id == 2
    assert extracted_result.athlete.name == "Petra Tester"
    assert float(extracted_result.wind) == 2.1
    assert result.location == "Zürich"
    assert len(extracted_result.athlete.results) == 1

    extracted_athlete: Athlete = session.query(Athlete).filter(Athlete.id == 1).first()
    assert len(extracted_athlete.results) == 0


def test_delete_result(session):
    result = Result(
        athlete_id=1,
        club_id=1,
        event_id=1,
        discipline_id=1,
        performance=1000,
        wind=1.4,
        rank="1f1",
        location="Bern",
        date=date.fromisoformat("2023-10-10"),
        homologated=True,
    )
    session.add(result)
    session.commit()

    assert session.query(Result).filter(Result.id == 1).first() is not None

    session.delete(result)
    session.commit()

    assert session.query(Result).filter(Result.id == 1).first() is None
