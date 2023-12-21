# pylint: disable=redefined-outer-name
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from track_insights.database.models import Log
from track_insights.database.models.log import LogType


@pytest.fixture(autouse=True)
def session():
    engine = create_engine("sqlite:///:memory:", echo=True)
    sess = sessionmaker(bind=engine)()

    Log.metadata.create_all(engine)

    yield sess

    sess.close()
    engine.dispose()


def test_add_log(session):
    log = Log(name="Insertion", description="Longer Description")
    session.add(log)
    session.commit()

    extracted_log: Log = session.query(Log).filter(Log.id == 1).first()

    assert extracted_log is not None
    assert extracted_log.name == "Insertion"
    assert extracted_log.description == "Longer Description"
    assert extracted_log.log_type == LogType.INFO


def test_update_log(session):
    log = Log(name="Insertion", description="Longer Description")
    session.add(log)
    session.commit()

    log.log_type = LogType.CRITICAL
    session.commit()

    extracted_log: Log = session.query(Log).filter(Log.id == 1).first()
    assert extracted_log is not None
    assert extracted_log.log_type == LogType.CRITICAL


def test_delete_log(session):
    log = Log(name="Insertion", description="Longer Description")
    session.add(log)
    session.commit()

    assert session.query(Log).filter(Log.id == 1).first() is not None

    session.delete(log)
    session.commit()

    assert session.query(Log).filter(Log.id == 1).first() is None
