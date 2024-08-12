# pylint: disable=redefined-outer-name
from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from track_insights.database.models import Athlete


@pytest.fixture(autouse=True)
def session():
    engine = create_engine("sqlite:///:memory:", echo=True)
    sess = sessionmaker(bind=engine)()

    Athlete.metadata.create_all(engine)

    yield sess

    sess.close()
    engine.dispose()


def test_add_athlete(session):
    athlete = Athlete(
        athlete_code="Code_123",
        name="Max Mustermann",
        birthdate=date.fromisoformat("2000-02-15"),
        nationality="SUI",
        latest_date=date.fromisoformat("2023-10-10"),
    )
    session.add(athlete)
    session.commit()

    extracted_athlete: Athlete = session.query(Athlete).filter(Athlete.id == 1).first()

    assert extracted_athlete is not None
    assert extracted_athlete.athlete_code == "Code_123"
    assert extracted_athlete.name == "Max Mustermann"
    assert extracted_athlete.birthdate
    assert extracted_athlete.birthdate == date.fromisoformat("2000-02-15")
    assert extracted_athlete.nationality == "SUI"
    assert extracted_athlete.latest_date
    assert extracted_athlete.latest_date == date.fromisoformat("2023-10-10")
    assert extracted_athlete.results == []


def test_constraints_athlete(session):
    athlete1 = Athlete(
        athlete_code="Code_123",
        name="Max Mustermann",
        birthdate=date.fromisoformat("2000-02-15"),
        nationality="SUI",
        latest_date=date.fromisoformat("2023-10-10"),
    )

    athlete2 = Athlete(
        athlete_code="Code_456",
        name="Petra Muster",
        birthdate=date.fromisoformat("2002-04-15"),
        nationality="GER",
        latest_date=date.fromisoformat("2023-09-08"),
    )

    session.add(athlete1)
    session.add(athlete2)
    session.commit()

    assert athlete1.id == 1
    assert athlete2.id == 2

    athlete2.athlete_code = "Code_123"

    with pytest.raises(IntegrityError):
        session.commit()


def test_update_athlete(session):
    athlete = Athlete(
        athlete_code="Code_123",
        name="Max Mustermann",
        birthdate=date.fromisoformat("2000-02-15"),
        nationality="SUI",
        latest_date=date.fromisoformat("2023-10-10"),
    )
    session.add(athlete)
    session.commit()

    athlete.name = "Petra Testing"
    athlete.nationality = "GER"
    session.commit()

    extracted_athlete: Athlete = session.query(Athlete).filter(Athlete.id == 1).first()
    assert extracted_athlete is not None
    assert extracted_athlete.name == "Petra Testing"
    assert extracted_athlete.nationality == "GER"

    athlete.latest_date += timedelta(days=5)
    session.commit()

    assert session.query(Athlete).filter(Athlete.id == 1).first().latest_date == date.fromisoformat("2023-10-15")


def test_delete_athlete(session):
    athlete = Athlete(
        athlete_code="Code_123",
        name="Max Mustermann",
        birthdate=date.fromisoformat("2000-02-15"),
        nationality="SUI",
        latest_date=date.fromisoformat("2023-10-10"),
    )
    session.add(athlete)
    session.commit()

    assert session.query(Athlete).filter(Athlete.id == 1).first() is not None

    session.delete(athlete)
    session.commit()

    assert session.query(Athlete).filter(Athlete.id == 1).first() is None
