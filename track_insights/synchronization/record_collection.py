import logging
import pathlib

import pandas as pd
from track_insights.database.models import Result
from track_insights.synchronization.record import Record

logger = logging.getLogger(__name__)


class RecordCollection:
    """
    This class represents a collection of records. It hence represents a bestlist or a list of results from
    the database.
    """

    def __init__(self, records: list[Record]):
        self.records = records

    @classmethod
    def from_dataframe(
        cls, df: pd.DataFrame, anomaly_file: pathlib.Path, ignored_entries: set[str]
    ) -> "RecordCollection":
        """
        Parses a DataFrame to a RecordCollection object.

        :param df: DataFrame to parse.
        :param anomaly_file: file to write anomalies to.
        :param ignored_entries: entries to ignore.
        :return: a new RecordCollection object.
        """

        # Get the list of columns in the DataFrame
        columns: set[str] = set(df.columns.tolist())

        records = [Record.from_dataframe_row(row, columns) for _, row in df.iterrows()]
        valid_records: list[Record] = []

        invalid_idx: list[int] = []
        for idx, record in enumerate(records):
            if record.is_valid():
                valid_records.append(record)
            else:
                record_json = df.iloc[idx].to_json()

                if record_json not in ignored_entries:
                    invalid_idx.append(idx)

        if len(invalid_idx) > 0:
            logger.warning(f"Found {len(invalid_idx)} invalid records.")
            df.iloc[invalid_idx].to_json(anomaly_file, orient="records", lines=True, mode="a")

        return cls(valid_records)

    @classmethod
    def from_database(cls, results: list[Result]) -> "RecordCollection":
        """
        Parses a list of database results to a RecordCollection object.

        :param results: list of database results.
        :return: a new RecordCollection object.
        """
        return cls([Record.from_database_row(result) for result in results])

    def sort_records(self, ascending: bool) -> None:
        """
        Sorts the records in the collection in place.

        :param ascending: whether to sort in ascending order.
        """
        # Sort by result, then by name
        self.records = sorted(
            self.records,
            key=lambda record: (
                (1 if ascending else -1) * record.performance,
                record.event_date,
                record.athlete,
                record.event,
                record.rank,
            ),
        )

    def sanity_check_results(self, ascending: bool) -> bool:
        """
        Checks if the records are sorted in the correct performance order.

        :param ascending: whether to check for ascending or descending order.
        :return: whether the records are sorted in the correct order.
        """
        if len(self) <= 1:
            return True
        if ascending:
            return all(self[i].performance <= self[i + 1].performance for i in range(len(self) - 1))
        return all(self[i].performance >= self[i + 1].performance for i in range(len(self) - 1))

    def __getitem__(self, index: int) -> Record:
        return self.records[index]

    def __setitem__(self, index: int, value: Record) -> None:
        assert value.is_valid(), "Can only insert valid records"

        self.records[index] = value

    def __delitem__(self, index: int) -> None:
        del self.records[index]

    def __len__(self) -> int:
        return len(self.records)
