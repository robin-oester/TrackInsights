# pylint: disable=redefined-outer-name
from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from track_insights.database.models import Event


@pytest.fixture(autouse=True)
def session():
    engine = create_engine("sqlite:///:memory:", echo=True)
    sess = sessionmaker(bind=engine)()

    Event.metadata.create_all(engine)

    yield sess

    sess.close()
    engine.dispose()


def test_add_event(session):
    event = Event(event_code="EvtCode_123", name="Test Event", latest_date=date.fromisoformat("2023-05-06"))
    session.add(event)
    session.commit()

    extracted_event: Event = session.query(Event).filter(Event.id == 1).first()

    assert extracted_event is not None
    assert extracted_event.event_code == "EvtCode_123"
    assert extracted_event.name == "Test Event"
    assert extracted_event.latest_date
    assert extracted_event.latest_date == date.fromisoformat("2023-05-06")
    assert extracted_event.results == []


def test_constraints_event(session):
    event1 = Event(event_code="EvtCode_123", name="Test Event", latest_date=date.fromisoformat("2023-05-06"))

    event2 = Event(event_code="EvtCode_456", name="Test Event 2", latest_date=date.fromisoformat("2023-05-06"))
    session.add(event1)
    session.add(event2)
    session.commit()

    assert event1.id == 1
    assert event2.id == 2

    event2.event_code = "EvtCode_123"

    with pytest.raises(IntegrityError):
        session.commit()


def test_update_event(session):
    event = Event(event_code="EvtCode_123", name="Test Event", latest_date=date.fromisoformat("2023-05-06"))
    session.add(event)
    session.commit()

    event.event_code = "Test_Code"
    session.commit()

    extracted_event: Event = session.query(Event).filter(Event.id == 1).first()
    assert extracted_event is not None
    assert extracted_event.event_code == "Test_Code"

    event.latest_date += timedelta(days=15)
    session.commit()

    assert session.query(Event).filter(Event.id == 1).first().latest_date == date.fromisoformat("2023-05-21")


def test_delete_club(session):
    event = Event(event_code="EvtCode_123", name="Test Event", latest_date=date.fromisoformat("2023-05-06"))
    session.add(event)
    session.commit()

    assert session.query(Event).filter(Event.id == 1).first() is not None

    session.delete(event)
    session.commit()

    assert session.query(Event).filter(Event.id == 1).first() is None
