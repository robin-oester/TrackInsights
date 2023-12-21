# pylint: disable=redefined-outer-name
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from track_insights.database.models import Discipline, DisciplineConfiguration


@pytest.fixture(autouse=True)
def session():
    engine = create_engine("sqlite:///:memory:", echo=True)
    sess = sessionmaker(bind=engine)()

    DisciplineConfiguration.metadata.create_all(engine)
    Discipline.metadata.create_all(engine)

    yield sess

    sess.close()
    engine.dispose()


def test_add_discipline(session):
    discipline_config = DisciplineConfiguration(
        name="Weit",
        ascending=False,
    )

    discipline = Discipline(
        discipline_code="Test_Discipline_123",
        config=discipline_config,
        indoor=False,
        male=True,
    )

    session.add(discipline_config)
    session.add(discipline)
    session.commit()

    extracted_discipline: Discipline = session.query(Discipline).filter(Discipline.id == 1).first()

    assert extracted_discipline is not None
    assert extracted_discipline.discipline_code == "Test_Discipline_123"
    assert extracted_discipline.male
    assert not extracted_discipline.indoor
    assert extracted_discipline.config.name == "Weit"
    assert not extracted_discipline.config.ascending
    assert extracted_discipline.results == []


def test_constraints_discipline(session):
    discipline_config = DisciplineConfiguration(
        name="Weit",
        ascending=False,
    )

    discipline1 = Discipline(
        discipline_code="Test_Discipline_123",
        config=discipline_config,
        indoor=False,
        male=True,
    )

    discipline2 = Discipline(
        discipline_code="Test_Discipline_123",
        config=discipline_config,
        indoor=True,
        male=False,
    )

    session.add(discipline_config)
    session.add(discipline1)
    session.add(discipline2)
    session.commit()

    assert discipline1.id == 1
    assert discipline2.id == 2

    discipline2.indoor = False
    discipline2.male = True

    with pytest.raises(IntegrityError):
        session.commit()


def test_update_discipline(session):
    discipline_config = DisciplineConfiguration(
        name="Weit",
        ascending=False,
    )

    discipline = Discipline(
        discipline_code="Test_Discipline_123",
        config=discipline_config,
        indoor=False,
        male=True,
    )

    session.add(discipline_config)
    session.add(discipline)
    session.commit()

    discipline.config.name = "100m"
    discipline.indoor = True
    session.commit()

    extracted_config: DisciplineConfiguration = (
        session.query(DisciplineConfiguration).filter(DisciplineConfiguration.id == 1).first()
    )

    assert extracted_config is not None
    assert extracted_config.name == "100m"

    extracted_discipline: Discipline = session.query(Discipline).filter(Discipline.id == 1).first()
    assert extracted_discipline is not None
    assert extracted_discipline.config.id == 1
    assert extracted_discipline.indoor


def test_delete_discipline(session):
    discipline_config = DisciplineConfiguration(
        name="Weit",
        ascending=False,
    )

    discipline = Discipline(
        discipline_code="Test_Discipline_123",
        config=discipline_config,
        indoor=False,
        male=True,
    )

    session.add(discipline_config)
    session.add(discipline)
    session.commit()

    assert session.query(Discipline).filter(Discipline.id == 1).first() is not None

    session.delete(discipline_config)

    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    session.delete(discipline)
    session.delete(discipline_config)
    session.commit()

    assert session.query(Discipline).count() == 0
    assert session.query(DisciplineConfiguration).count() == 0
