# pylint: disable=unsubscriptable-object
from datetime import date

from sqlalchemy import CHAR, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from track_insights.database.database_base import DatabaseBase


class Athlete(DatabaseBase):
    """Athlete model."""

    __tablename__ = "athletes"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    athlete_code: Mapped[str] = mapped_column(String(length=50), unique=True)
    name: Mapped[str] = mapped_column(String(length=50))
    birthdate: Mapped[date]
    nationality: Mapped[str] = mapped_column(CHAR(length=3))
    latest_date: Mapped[date]
    results: Mapped[list["Result"]] = relationship(back_populates="athlete", lazy="select")  # noqa: F821
    __table_args__ = (Index("name", "birthdate", "nationality"), {"extend_existing": True})

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Athlete {self.id}>"
