# pylint: disable=unsubscriptable-object
import enum
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from track_insights.database.database_base import DatabaseBase


class DisciplineType(enum.Enum):
    SHORT_TRACK = "SHORT_TRACK"
    LONG_TRACK = "LONG_TRACK"
    THROW = "THROW"
    JUMP = "JUMP"
    MULTI = "MULTI"
    DISTANCE = "DISTANCE"


class DisciplineConfiguration(DatabaseBase):
    """Discipline lookup model."""

    __tablename__ = "discipline_configs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(length=30), unique=True)
    discipline_type: Mapped[DisciplineType] = mapped_column(
        Enum(DisciplineType, name="discipline_type_enum"), default=DisciplineType.SHORT_TRACK, nullable=False
    )
    disciplines: Mapped[list["Discipline"]] = relationship(back_populates="config")
    __table_args__ = {"extend_existing": True}

    def is_ascending(self) -> bool:
        """
        Whether the discipline is ascending, i.e., the lower the value, the better the performance.
        """

        return self.discipline_type in {DisciplineType.SHORT_TRACK, DisciplineType.LONG_TRACK}

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<DisciplineConfiguration {self.id}>"


class Discipline(DatabaseBase):
    """Discipline model."""

    __tablename__ = "disciplines"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    config_id: Mapped[int] = mapped_column(ForeignKey(DisciplineConfiguration.id))
    discipline_code: Mapped[str] = mapped_column(String(50))
    indoor: Mapped[bool]
    male: Mapped[bool]
    ignore: Mapped[bool] = mapped_column(default=False)
    score_identifier: Mapped[Optional[str]] = mapped_column(String(length=30), default=None)
    config: Mapped[DisciplineConfiguration] = relationship(back_populates="disciplines", lazy="joined")
    results: Mapped[list["Result"]] = relationship(back_populates="discipline", lazy="select")  # noqa: F821
    __table_args__ = (UniqueConstraint("discipline_code", "indoor", "male"), {"extend_existing": True})

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Discipline {self.id}>"
