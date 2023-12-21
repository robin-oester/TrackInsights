from datetime import date

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from track_insights.database.database_base import DatabaseBase


class Event(DatabaseBase):
    """Event model."""

    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_code: Mapped[str] = mapped_column(String(length=50), unique=True)
    name: Mapped[str] = mapped_column(String(length=100))
    results: Mapped[list["Result"]] = relationship(back_populates="event", lazy="select")  # noqa: F821
    latest_date: Mapped[date]
    __table_args__ = {"extend_existing": True}

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Event {self.id}>"
