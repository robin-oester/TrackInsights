from datetime import date
from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from track_insights.database.database_base import DatabaseBase


class Club(DatabaseBase):
    """Club model."""

    __tablename__ = "clubs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    club_code: Mapped[Optional[str]] = mapped_column(String(length=50), unique=True)
    name: Mapped[str] = mapped_column("name", String(length=50), unique=True)
    latest_date: Mapped[date]
    results: Mapped[list["Result"]] = relationship(back_populates="club", lazy="select")  # noqa: F821
    __table_args__ = {"extend_existing": True}

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Club {self.id}>"
