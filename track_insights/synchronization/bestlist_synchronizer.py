import logging
import pathlib
from typing import Optional

import pandas as pd
import sqlalchemy
from sqlalchemy import and_
from sqlalchemy.orm import Session
from track_insights.database import DatabaseConnection
from track_insights.database.models import Athlete, Club, Discipline, Event, Result
from track_insights.scores import ScoreList
from track_insights.scraping import BestlistCategory, BestlistColumn, ScrapeConfig
from track_insights.synchronization.record import Record
from track_insights.synchronization.record_collection import RecordCollection
from track_insights.synchronization.synchronization_statistics import SynchronizationStatistics

logger = logging.getLogger(__name__)


class BestlistSynchronizer:
    """
    This class can be considered as the "brain" of this system. It is responsible for the synchronization of the
    bestlist with the local database by processing the scraped dataframe.
    """

    def __init__(
        self, config: dict, scrape_config: ScrapeConfig, bestlist: pd.DataFrame, verbose: bool = False
    ) -> None:
        """
        Initializes the bestlist synchronizer.

        :param config: the system configuration dictionary.
        :param scrape_config: the scrape configuration.
        :param bestlist: the scraped bestlist dataframe.
        :param verbose: whether to print additional information.
        """

        self.config = config
        self.scrape_config = scrape_config
        self.original_bestlist = bestlist.drop(columns=[BestlistColumn.NUMBER])  # We do not need the bestlist rank
        self.bl_limit_reached = len(self.original_bestlist.index) == self.scrape_config.amount
        self.verbose = verbose

    # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    def synchronize(self, anomaly_path: pathlib.Path, ignored_entries: set[str]) -> SynchronizationStatistics:
        """
        Synchronizes the bestlist with the local database.

        :param anomaly_path: the path to the anomaly log file.
        :param ignored_entries: the set of ignored entries.
        :return: the synchronization statistics.
        """

        if self.verbose:
            logger.info(f"Processing bestlist for scrape config {self.scrape_config}")
        bestlist_df = self.original_bestlist.copy(deep=True)

        bestlist_records = RecordCollection.from_dataframe(bestlist_df, anomaly_path, ignored_entries)

        # whether the discipline follow an ascending order (higher results are worse)
        ascending = self.scrape_config.discipline.config.ascending

        # sanity check yields error if the discipline is misconfigured or the bestlist is off
        if not bestlist_records.sanity_check_results(ascending):
            raise ValueError("Results are not monotonically increasing/decreasing")

        # read the corresponding records from the database
        database_records = self._fetch_records_from_database(
            self.scrape_config.discipline, bestlist_records[-1].performance if len(bestlist_records) > 0 else None
        )

        bestlist_records.sort_records(ascending)
        database_records.sort_records(ascending)
        with DatabaseConnection(self.config) as database:
            insertion_mask, deletion_mask, similarities = self._compare_records(
                bestlist_records, database_records, ascending
            )

            # if we did not find exact match of the bestlist record, we greedily search for a similar database record.
            total_updates = 0
            for bl_idx, db_idx in similarities:
                if insertion_mask[bl_idx] and deletion_mask[db_idx]:
                    # we found a corresponding mapping and apply the update, which saves us a delete and insert.
                    insertion_mask[bl_idx] = False
                    deletion_mask[db_idx] = False

                    result: Result = database.session.get(Result, database_records[db_idx].id)
                    total_updates += self._update_entries(
                        result.athlete, result.club, result.event, bestlist_records[bl_idx]
                    )
                    database.session.flush()

            # delete records
            deleted_records: list[Record] = []
            deletion_keys: list[int] = []
            for delete_record in [
                record
                for record, delete in zip(database_records.records, deletion_mask)
                if delete and not record.manual
            ]:
                deleted_records.append(delete_record)
                deletion_keys.append(delete_record.id)

            database.session.query(Result).filter(Result.id.in_(deletion_keys)).delete(False)

            # insert records
            insertion_records = [record for record, insert in zip(bestlist_records.records, insertion_mask) if insert]
            sync_statistics = self._insert_records(
                database.session,
                insertion_records,
                self.scrape_config.discipline,
                BestlistCategory.get_age_bounds(self.scrape_config.category),
            )

            sync_statistics.updates += total_updates
            database.session.commit()

        return sync_statistics

    def _insert_records(
        self, session: Session, records: list[Record], discipline: Discipline, age_bounds: tuple[int, int]
    ) -> SynchronizationStatistics:
        """
        Inserts the records to the database.
        The statistics include the amount of added athletes, clubs and events
        as well as the total amount of modifications (corresponds to the number of updates).

        :param records: the records to be inserted.
        :param discipline: the discipline.
        :return: synchronization statistics.
        """

        added_results, added_athletes, added_clubs, added_events = 0, 0, 0, 0
        total_modifications = 0

        score_list: Optional[ScoreList] = None
        if discipline.score_identifier is not None and len(records) > 0:
            score_list = ScoreList(discipline)

        # check whether we need to insert new athletes, clubs or event then we apply the value updates from the bestlist
        for record in records:
            athlete: Athlete = session.query(Athlete).filter(Athlete.athlete_code == record.athlete_code).first()
            result_date = record.event_date
            if not athlete:
                # insert new athlete
                added_athletes += 1
                athlete = Athlete(
                    name=record.athlete,
                    birthdate=record.birthdate,
                    nationality=record.nationality,
                    athlete_code=record.athlete_code,
                    latest_date=result_date,
                )
                session.add(athlete)

            club_code = record.club_code

            club: Club
            existing_club: Optional[Club]
            if club_code != "":
                existing_club = session.query(Club).filter(Club.club_code == club_code).first()
            else:
                existing_club = session.query(Club).filter(Club.name == record.club).first()
            if existing_club is not None:
                club = existing_club
            else:
                # insert new club
                added_clubs += 1
                club = Club(
                    name=record.club,
                    club_code=club_code or None,
                    latest_date=result_date,
                )
                session.add(club)

            event: Event = session.query(Event).filter(Event.event_code == record.event_code).first()
            if not event:
                # insert new event
                added_events += 1
                event = Event(
                    name=record.event,
                    event_code=record.event_code,
                    latest_date=result_date,
                )
                session.add(event)

            total_modifications += self._update_entries(athlete, club, event, record)

            # Some results are present in the wrong category. We account for this case by searching the corresponding
            # result in our database. If it is not found, we tag the result as being inserted manually.
            diff = record.event_date.year - record.birthdate.year
            manual = False
            if diff < age_bounds[0] or diff >= age_bounds[1]:
                manual = True
                found_result = (
                    session.query(Result)
                    .filter(
                        Result.discipline_id == discipline.id,
                        Result.athlete_id == athlete.id,
                        Result.club_id == club.id,
                        Result.event_id == event.id,
                        Result.performance == record.performance,
                        Result.wind == record.wind,
                        Result.rank == record.rank,
                        Result.location == record.location,
                        Result.date == result_date,
                        Result.homologated.is_(not record.not_homologated),
                    )
                    .first()
                )
                if found_result:
                    found_result.manual = True
                    session.flush()
                    continue

            # otherwise, we insert a new result
            result = Result(
                athlete=athlete,
                club=club,
                event=event,
                discipline_id=discipline.id,
                performance=record.performance,
                wind=record.wind,
                rank=record.rank,
                location=record.location,
                date=result_date,
                homologated=not record.not_homologated,
                manual=manual,
                points=score_list.find_score(record.performance) if score_list is not None else 0,
            )

            added_results += 1
            session.add(result)
            session.flush()

        return SynchronizationStatistics(
            added_records=added_results,
            added_athletes=added_athletes,
            added_clubs=added_clubs,
            added_events=added_events,
            updates=total_modifications,
        )

    # pylint: disable=too-many-locals
    def _compare_records(
        self, bl_records: RecordCollection, db_records: RecordCollection, ascending: bool
    ) -> tuple[list[bool], list[bool], list[tuple[int, int]]]:
        """
        Compares the bestlist records to the database records.
        This method returns the insertion mask (for the bestlist records), the deletion mask (for the database records),
        and a list of (bl_record, db_record)-pairs consisting of bestlist and database records, which capture the same
        underlying result. Note that both record arrays must be sorted in descending performance order.

        :param bl_records: the records from the bestlist.
        :param db_records: the records from the database.
        :param ascending: whether higher results are considered better.
        :return: list of pairs of indices from the bestlist and database.
        """

        amount_bestlist_records = len(bl_records)
        amount_database_records = len(db_records)

        insertion_mask = [True for _ in range(amount_bestlist_records)]
        deletion_mask = [True for _ in range(amount_database_records)]

        curr_bl_idx = 0
        curr_db_idx = 0

        # list of 'similar' records from the bestlist and database.
        similar_records: list[tuple[int, int]] = []
        while curr_bl_idx < amount_bestlist_records:
            curr_bl_record = bl_records[curr_bl_idx]

            # check whether the bestlist contains duplicates
            prev_bl_idx = curr_bl_idx - 1
            if prev_bl_idx >= 0 and bl_records[prev_bl_idx] == curr_bl_record:
                insertion_mask[curr_bl_idx] = False
                curr_bl_idx += 1
                continue
            if curr_db_idx >= amount_database_records:
                curr_bl_idx += 1
                continue

            curr_db_record = db_records[curr_db_idx]

            # check if a match is even possible (same performance for bestlist and database record).
            curr_bl_result = curr_bl_record.performance
            curr_db_result = curr_db_record.performance
            if ((curr_db_result > curr_bl_result) and ascending) or (
                (curr_db_result < curr_bl_result) and not ascending
            ):
                curr_bl_idx += 1
                continue

            if ((curr_bl_result > curr_db_result) and ascending) or (
                (curr_bl_result < curr_db_result) and not ascending
            ):
                curr_db_idx += 1
                continue

            # here: curr_bl_result == curr_db_result
            # find the database record that matches the bestlist record.
            next_db_idx = curr_db_idx
            while next_db_idx < amount_database_records and db_records[next_db_idx].performance == curr_bl_result:
                next_db_record = db_records[next_db_idx]
                if curr_bl_record == next_db_record:
                    # an exact match is found, no need to insert or delete.
                    insertion_mask[curr_bl_idx] = False
                    deletion_mask[next_db_idx] = False

                    if next_db_idx == curr_db_idx:
                        # in this case, we can safely proceed to the next database index.
                        curr_db_idx += 1
                    break
                if curr_bl_record.is_similar(next_db_record):
                    # all attributes regarding the result are equal, add to the similarity list.
                    similar_records.append((curr_bl_idx, next_db_idx))
                next_db_idx += 1

            # in any case, we proceed with the next bestlist record.
            curr_bl_idx += 1

        # cannot safely delete records that are out of bestlist range
        if self.bl_limit_reached:
            last_bl_result = bl_records[-1].performance
            for i in range(amount_database_records):
                db_result = db_records[amount_database_records - 1 - i].performance
                if (db_result >= last_bl_result and ascending) or (db_result <= last_bl_result and not ascending):
                    deletion_mask[amount_database_records - 1 - i] = False

        return insertion_mask, deletion_mask, similar_records

    @staticmethod
    def _update_entries(athlete: Athlete, club: Club, event: Event, record: Record) -> int:
        """
        Update database records (athlete, club and event) according to a record from the bestlist.
        We only update an entry, if the bestlist result event_date is later or equal to the latest event_date associated
        with the entry. We only increase the update count with changes to fields that are present in the bestlist.

        :param athlete: the athlete associated with the corresponding database record.
        :param club: the club associated with the corresponding database record.
        :param event: the event associated with the corresponding database record.
        :param record: the record which forms the source of truth for the record.
        :return: the total number of performed updates.
        """

        result_date = record.event_date
        amount_updates = 0
        if result_date >= athlete.latest_date:
            if athlete.name != record.athlete:
                athlete.name = record.athlete
                amount_updates += 1
            if athlete.birthdate != record.birthdate:
                athlete.birthdate = record.birthdate
                amount_updates += 1
            if athlete.nationality != record.nationality:
                athlete.nationality = record.nationality
                amount_updates += 1
            athlete.latest_date = result_date

        if result_date >= club.latest_date:
            if club.name != record.club:
                club.name = record.club
                amount_updates += 1
            club.latest_date = result_date

        if result_date >= event.latest_date:
            if event.name != record.event:
                event.name = record.event
                amount_updates += 1
            event.latest_date = result_date

        return amount_updates

    def _fetch_records_from_database(self, discipline: Discipline, last_result: Optional[int]) -> RecordCollection:
        """
        Reads the results from the database.

        :param discipline: the discipline from which the results are fetched.
        :return: the database record collection.
        """

        with DatabaseConnection(self.config) as database:
            year = self.scrape_config.year
            lower_bound, upper_bound = BestlistCategory.get_age_bounds(self.scrape_config.category)
            results: list[Result] = (
                database.session.query(Result)
                .join(Athlete, Result.athlete)
                .join(Event, Result.event)
                .filter(
                    Result.discipline_id == discipline.id,
                    (
                        (
                            Result.performance <= last_result
                            if discipline.config.ascending
                            else Result.performance >= last_result
                        )
                        if last_result is not None
                        else True
                    ),
                    sqlalchemy.extract("year", Result.date) == year if year is not None else True,
                    Result.homologated if self.scrape_config.only_homologated else True,
                    Result.wind <= 2.0 if Result.wind and not self.scrape_config.allow_wind else True,
                    and_(
                        sqlalchemy.extract("year", Result.date) - sqlalchemy.extract("year", Athlete.birthdate)
                        >= lower_bound,
                        sqlalchemy.extract("year", Result.date) - sqlalchemy.extract("year", Athlete.birthdate)
                        < upper_bound,
                    ),
                )
                .order_by(Result.performance.asc() if discipline.config.ascending else Result.performance.desc())
                .all()
            )
            return RecordCollection.from_database(results)
