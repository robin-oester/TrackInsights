# pylint: disable=unsubscriptable-object
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column
from track_insights.database.database_base import DatabaseBase


class LogType(enum.Enum):
    INFO = 1
    WARNING = 2
    CRITICAL = 3


class Log(DatabaseBase):
    """Log model."""

    __tablename__ = "logs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())  # pylint: disable=not-callable
    log_type: Mapped[str] = mapped_column(Enum(LogType), default=LogType.INFO)
    name: Mapped[str] = mapped_column(String(length=30))
    description: Mapped[Optional[str]] = mapped_column(String(length=200))
    __table_args__ = {"extend_existing": True}

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Log {self.id}>"
