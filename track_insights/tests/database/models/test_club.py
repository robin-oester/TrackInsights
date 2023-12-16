from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from track_insights.database.models import Club


@pytest.fixture(autouse=True)
def session():
    engine = create_engine("sqlite:///:memory:", echo=True)
    sess = sessionmaker(bind=engine)()

    Club.metadata.create_all(engine)

    yield sess

    sess.close()
    engine.dispose()


def test_add_club(session):
    club = Club(
        club_code="Code_123",
        name="LV Muster",
        latest_date=date.fromisoformat("2023-01-11")
    )
    session.add(club)
    session.commit()

    extracted_club: Club = session.query(Club).filter(Club.id == 1).first()

    assert extracted_club is not None
    assert extracted_club.club_code == "Code_123"
    assert extracted_club.name == "LV Muster"
    assert extracted_club.latest_date
    assert extracted_club.latest_date == date.fromisoformat("2023-01-11")
    assert extracted_club.results == []


def test_constraints_club(session):
    club1 = Club(
        club_code="Code_123",
        name="LV Muster",
        latest_date=date.fromisoformat("2023-01-11")
    )
    club2 = Club(
        club_code="Code_456",
        name="LC Tester",
        latest_date=date.fromisoformat("2023-01-11")
    )

    session.add(club1)
    session.add(club2)
    session.commit()

    assert club1.id == 1
    assert club2.id == 2

    club2.club_code = "Code_123"

    with pytest.raises(IntegrityError):
        session.commit()


def test_update_club(session):
    club = Club(
        club_code="Code_123",
        name="LV Muster",
        latest_date=date.fromisoformat("2023-01-31")
    )
    session.add(club)
    session.commit()

    club.name = "LC Buchs"
    session.commit()

    extracted_club: Club = session.query(Club).filter(Club.id == 1).first()
    assert extracted_club is not None
    assert extracted_club.name == "LC Buchs"

    club.latest_date += timedelta(days=1)
    session.commit()

    assert session.query(Club).filter(Club.id == 1).first().latest_date == date.fromisoformat("2023-02-01")


def test_delete_club(session):
    club = Club(
        club_code="Code_123",
        name="LV Muster",
        latest_date=date.fromisoformat("2023-01-31")
    )
    session.add(club)
    session.commit()

    assert session.query(Club).filter(Club.id == 1).first() is not None

    session.delete(club)
    session.commit()

    assert session.query(Club).filter(Club.id == 1).first() is None
