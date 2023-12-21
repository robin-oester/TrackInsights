from datetime import date, datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index, Numeric, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from track_insights.database.database_base import DatabaseBase
from track_insights.database.models.athlete import Athlete
from track_insights.database.models.club import Club
from track_insights.database.models.discipline import Discipline
from track_insights.database.models.event import Event


class Result(DatabaseBase):
    """Result model."""

    __tablename__ = "results"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey(Athlete.id))
    club_id: Mapped[int] = mapped_column(ForeignKey(Club.id))
    event_id: Mapped[int] = mapped_column(ForeignKey(Event.id))
    discipline_id: Mapped[int] = mapped_column(ForeignKey(Discipline.id))
    performance: Mapped[int]
    wind: Mapped[Optional[float]] = mapped_column(Numeric(precision=3, scale=1))
    rank: Mapped[Optional[str]] = mapped_column(String(10))
    location: Mapped[str] = mapped_column(String(50))
    date: Mapped[date]
    homologated: Mapped[bool] = mapped_column(default=True)
    ignore: Mapped[bool] = mapped_column(default=False)  # result parses but is invalid at swiss-athletics
    manual: Mapped[bool] = mapped_column(default=False)  # result is captured manually
    insert_date: Mapped[datetime] = mapped_column(server_default=func.now())  # pylint: disable=not-callable
    points: Mapped[int] = mapped_column(SmallInteger, default=0)
    athlete: Mapped["Athlete"] = relationship(back_populates="results", lazy="select")
    club: Mapped["Club"] = relationship(back_populates="results", lazy="select")
    event: Mapped["Event"] = relationship(back_populates="results", lazy="select")
    discipline: Mapped["Discipline"] = relationship(back_populates="results", lazy="select")
    __table_args__ = (
        Index("ix_date", "date"),
        Index("ix_insert_date", "insert_date"),
        Index("ix_points", "points"),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Result {self.id}>"
