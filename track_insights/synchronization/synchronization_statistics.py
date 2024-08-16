from dataclasses import dataclass, field

from track_insights.synchronization.record import Record


@dataclass
class SynchronizationStatistics:
    """
    This class holds the synchronization statistics gathered through synchronizing the bestlist records with the
    local database.
    """

    added_records: int = 0
    added_athletes: int = 0
    added_clubs: int = 0
    added_events: int = 0
    updates: int = 0
    deletions: list[Record] = field(default_factory=list)

    def add(self, other: "SynchronizationStatistics") -> None:
        self.added_records += other.added_records
        self.added_athletes += other.added_athletes
        self.added_clubs += other.added_clubs
        self.added_events += other.added_events
        self.updates += other.updates
        self.deletions += other.deletions
