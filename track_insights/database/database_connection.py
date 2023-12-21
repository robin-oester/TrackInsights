"""Database connection context manager."""

from __future__ import annotations

import logging

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker
from track_insights.database import DatabaseBase

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Database connection context manager."""

    def __init__(self, config: dict) -> None:
        """
        Initialize the database connection.

        :param config: system configuration.
        """
        self.config = config
        self.drivername: str = self.config["database"]["drivername"]
        self.username: str = self.config["database"]["username"]
        self.password: str = self.config["database"]["password"]
        self.host: str = self.config["database"]["host"]
        self.port: int = self.config["database"]["port"]
        self.database: str = self.config["database"]["database"]

    def __enter__(self) -> DatabaseConnection:
        """
        Create the engine and session.

        :return: the database connection.
        """
        self.setup_connection()
        return self

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb: Exception) -> None:
        """
        Close the session and dispose the engine.

        :param exc_type: exception type.
        :param exc_val: exception value.
        :param exc_tb: exception traceback.
        """
        self.terminate_connection()

    def create_tables(self) -> None:
        """
        Create all tables. Each table is represented by a class.

        All classes that inherit from Base are mapped to tables
        which are created in the database if they do not exist.

        The metadata is a collection of Table objects that inherit from Base and their associated
        schema constructs (such as Column objects, ForeignKey objects, and so on).
        """
        DatabaseBase.metadata.create_all(self.engine)

    def setup_connection(self) -> None:
        self.url = URL.create(
            drivername=self.drivername,
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )
        self.engine = create_engine(self.url)
        self.session: Session = sessionmaker(bind=self.engine)()

    def terminate_connection(self) -> None:
        self.session.close()
        self.engine.dispose()
