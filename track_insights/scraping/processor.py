import logging
import pathlib
import re

import pandas as pd
import numpy as np
import sqlalchemy
from sqlalchemy.orm import Session

from track_insights.database import DatabaseConnection
from track_insights.database.models import Result, Discipline, Athlete, Club, Event
from track_insights.scraping.bestlist_field import BestlistField
from track_insights.scraping.scrape_config import ScrapeConfig

HOURS_TO_HUNDREDTHS = 100 * 60 * 60
MINUTES_TO_HUNDREDTHS = 100 * 60
SECONDS_TO_HUNDREDTHS = 100

logger = logging.getLogger(__name__)


class Processor:

    def __init__(self, config: dict, scrape_config: ScrapeConfig, bestlist: pd.DataFrame, ignored_entries: set[str]):
        """
        Initializes the scraping.

        :param config: the system configuration.
        :param scrape_config: the scrape configuration.
        :param bestlist: the serialized bestlist.
        :param ignored_entries: the serialized entries that must be ignored.
        """
        self.config = config
        self.scrape_config = scrape_config
        self.original_bestlist = bestlist.drop(columns=[BestlistField.NUMBER.value])  # We do not need the bestlist rank
        self.ignored_entries = ignored_entries

        self.wind_relevant = BestlistField.WIND.value in bestlist.columns
        self.homologation_relevant = BestlistField.NOT_HOMOLOGATED.value in bestlist.columns

    def process(self, error_path: pathlib.Path) -> None:
        """
        Processes the bestlist by inserting the newly seen results and updating the changed ones.

        :param error_path: the path to the file where parsing errors are stored.
        """
        bestlist = self.original_bestlist.copy(True)
        logger.info(f"Processing bestlist for scrape config {self.scrape_config}")

        bestlist[BestlistField.DATE.value] = pd.to_datetime(bestlist[BestlistField.DATE.value], format="%d.%m.%Y", errors="coerce")
        bestlist[BestlistField.BIRTHDATE.value] = pd.to_datetime(bestlist[BestlistField.BIRTHDATE.value], format="%d.%m.%Y", errors="coerce")
        bestlist[BestlistField.RESULT.value] = bestlist[BestlistField.RESULT.value].map(self._parse_result)

        # masks all valid (parsable) records
        bestlist[BestlistField.VALID.value] = bestlist[BestlistField.DATE.value].notna() & \
                                        bestlist[BestlistField.BIRTHDATE.value].notna() & \
                                        (bestlist[BestlistField.RESULT.value] >= 0)

        if self.wind_relevant:
            # depending on the value for column wind, a record is marked as (in)valid
            # (-100, 100) -> valid, "" -> valid (np.nan), otherwise invalid
            wind_available = bestlist[BestlistField.WIND.value] != ""
            bestlist[BestlistField.WIND.value] = pd.to_numeric(bestlist[BestlistField.WIND.value], errors="coerce")
            oob = bestlist[BestlistField.WIND.value].between(-100, 100, inclusive="neither")  # out-of-bounds values
            bestlist[BestlistField.WIND.value] = bestlist[BestlistField.WIND.value].where(oob, np.nan)
            bestlist[BestlistField.VALID.value] &= ~(wind_available & bestlist[BestlistField.WIND.value].isna())

        if self.homologation_relevant:
            bestlist[BestlistField.NOT_HOMOLOGATED.value] = bestlist[BestlistField.NOT_HOMOLOGATED.value] == "X"

        if not bestlist[BestlistField.VALID.value].all():
            # store invalid records to json file
            invalid_records = self.original_bestlist[~bestlist[BestlistField.VALID.value]].copy()
            errors = invalid_records.to_json(orient="records", lines=True).split("\n")[:-1]  # do not capture final empty string
            invalid_records[BestlistField.SCRAPE_CONFIG.value] = self.scrape_config

            # remove ignored records
            removed_indices: list[int] = []
            for idx, error in enumerate(errors):
                if error in self.ignored_entries:
                    removed_indices.append(idx)
            invalid_records = invalid_records.drop(invalid_records.index[removed_indices])
            error_count = len(invalid_records.index)
            if error_count > 0:
                logger.warning(f"Found {error_count} invalid records.")
                invalid_records.to_json(error_path, orient="records", lines=True, mode="a")

        # from now on, bestlist only contains valid records
        bestlist = bestlist[bestlist[BestlistField.VALID.value]].drop(columns=BestlistField.VALID.value)

        # fetch the discipline
        with DatabaseConnection(self.config) as database:
            discipline: Discipline = database.session.query(Discipline).filter(
                Discipline.discipline_code == self.scrape_config.discipline_code,
                Discipline.indoor == self.scrape_config.indoor,
                Discipline.male == self.scrape_config.male
            ).first()

        if not discipline:
            logger.error(f"Could not find discipline with code {self.scrape_config.discipline_code}, "
                         f"indoor = {self.scrape_config.indoor}, "
                         f"male = {self.scrape_config.male}")
            return

        ascending = discipline.config.ascending
        sanity_check = self._sanity_check_results(bestlist, ascending)
        if not sanity_check:
            logger.error("Results are not monotonically increasing/decreasing!")
            return

        bl_records: np.recarray = bestlist.to_records(index=False, column_dtypes=BestlistField.get_mapping())
        db_records: np.recarray = self._read_results_from_database(discipline)

        with DatabaseConnection(self.config) as database:
            insertion_mask, deletion_mask, similarities = self._compare_records(bl_records, db_records, ascending)

            # if we did not find an exact match of the bestlist record, we greedily search for a similar database record.
            total_updates = 0
            for bl_idx, db_idx in similarities:
                if insertion_mask[bl_idx] and deletion_mask[db_idx]:
                    # we found a corresponding mapping and apply the update, which saves us a delete and insert.
                    insertion_mask[bl_idx] = False
                    deletion_mask[db_idx] = False

                    result: Result = database.session.get(Result, db_records[db_idx][BestlistField.ID.value])
                    total_updates += self._update_entries(result.athlete, result.club, result.event, bl_records[bl_idx])
                    database.session.flush()

            # delete records
            deletion_keys = db_records[deletion_mask][BestlistField.ID.value]
            database.session.query(Result).filter(Result.id.in_(deletion_keys)).delete(False)

            # insert records
            insertion_records = bl_records[insertion_mask]
            (added_athletes, added_clubs, added_events), amount_updates = self._insert_records(database.session, insertion_records, discipline.id)
            total_updates += amount_updates
            database.session.commit()

        if len(deletion_keys) > 0:
            logger.info(f"Deleting {len(deletion_keys)} key(s): {deletion_keys}.")
        if len(insertion_records) > 0:
            logger.info(
                f"Insertion Summary: {len(insertion_records)} record(s), {added_athletes} athlete(s), {added_clubs} club(s), {added_events} event(s).")
        if total_updates > 0:
            logger.info(f"Total Updates: {total_updates}.")

    def _insert_records(self, session: Session, records: np.recarray, discipline_id: int) -> ((int, int, int), int):
        """
        Inserts the records to the database.
        The statistics include the amount of added athletes, clubs and events
        as well as the total amount of modifications (corresponds to the number of updates).

        :param records: the records to be inserted.
        :param discipline_id: identifier of the discipline.
        :return: insertion/update statistics.
        """
        added_athletes, added_clubs, added_events = 0, 0, 0
        total_modifications = 0
        for record in records:
            athlete: Athlete = session.query(Athlete) \
                .filter(Athlete.athlete_code == record[BestlistField.ATHLETE_CODE.value]).first()
            result_date = record[BestlistField.DATE.value].item()
            if not athlete:
                # insert new athlete
                added_athletes += 1
                athlete = Athlete(name=record[BestlistField.ATHLETE.value],
                                  birthdate=record[BestlistField.BIRTHDATE.value].item(),
                                  nationality=record[BestlistField.NATIONALITY.value],
                                  athlete_code=record[BestlistField.ATHLETE_CODE.value],
                                  latest_date=result_date)
                session.add(athlete)

            club: Club = session.query(Club) \
                .filter(Club.club_code == record[BestlistField.CLUB_CODE.value]).first()
            if not club:
                # insert new club
                added_clubs += 1
                club = Club(name=record[BestlistField.CLUB.value],
                            club_code=record[BestlistField.CLUB_CODE.value],
                            latest_date=result_date)
                session.add(club)

            event: Event = session.query(Event) \
                .filter(Event.event_code == record[BestlistField.EVENT_CODE.value]).first()
            if not event:
                # insert new event
                added_events += 1
                event = Event(name=record[BestlistField.EVENT.value],
                              event_code=record[BestlistField.EVENT_CODE.value],
                              latest_date=result_date)
                session.add(event)

            total_modifications += self._update_entries(athlete, club, event, record)

            result = Result(
                athlete=athlete,
                club=club,
                event=event,
                discipline_id=discipline_id,
                performance=record[BestlistField.RESULT.value].item(),
                wind=None if np.isnan(record[BestlistField.WIND.value]) else record[BestlistField.WIND.value],
                rank=None if record[BestlistField.RANK.value] == "" else record[BestlistField.RANK.value],
                location=record[BestlistField.LOCATION.value],
                date=result_date,
                homologated=False if self.homologation_relevant and record[BestlistField.NOT_HOMOLOGATED.value] else True
            )
            session.add(result)
            session.flush()
        return (added_athletes, added_clubs, added_events), total_modifications

    def _compare_records(self, bl_records: np.recarray, db_records: np.recarray, ascending: bool) -> (np.ndarray, np.ndarray, list[(int, int)]):
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

        insertion_mask = np.ones(amount_bestlist_records).astype(bool)
        deletion_mask = np.ones(amount_database_records).astype(bool)

        curr_bl_idx = 0
        curr_db_idx = 0

        # list of similar records from the bestlist and database.
        similar_records: list[(int, int)] = []
        while curr_bl_idx < amount_bestlist_records:
            curr_bl_record = bl_records[curr_bl_idx]

            # check for duplicates in bestlist.
            prev_bl_idx = curr_bl_idx - 1
            if prev_bl_idx >= 0 and self._get_record_similarity(bl_records[prev_bl_idx], curr_bl_record) == 1:
                insertion_mask[curr_bl_idx] = False
                curr_bl_idx += 1
                continue
            elif curr_db_idx >= amount_database_records:
                curr_bl_idx += 1
                continue

            curr_db_record = db_records[curr_db_idx]

            # check if a match is even possible (same performance for bestlist and database record).
            curr_bl_result = curr_bl_record[BestlistField.RESULT.value]
            curr_db_result = curr_db_record[BestlistField.RESULT.value]
            if ((curr_db_result > curr_bl_result) and ascending) or \
                    ((curr_db_result < curr_bl_result) and not ascending):
                curr_bl_idx += 1
                continue

            if ((curr_bl_result > curr_db_result) and ascending) or \
                    ((curr_bl_result < curr_db_result) and not ascending):
                curr_db_idx += 1
                continue

            # here: curr_bl_result == curr_db_result
            # find the database record that matches the bestlist record.
            next_db_idx = curr_db_idx
            while next_db_idx < amount_database_records and db_records[next_db_idx][BestlistField.RESULT.value] == curr_bl_result:
                next_db_record = db_records[next_db_idx]
                similarity = self._get_record_similarity(curr_bl_record, next_db_record)
                if similarity == 1:
                    # an exact match is found, no need to insert or delete.
                    insertion_mask[curr_bl_idx] = False
                    deletion_mask[next_db_idx] = False
                    if next_db_idx == curr_db_idx:
                        curr_db_idx += 1
                    break
                elif similarity == 0:
                    # all attributes regarding the result are equal, add to the similarity list.
                    similar_records.append((curr_bl_idx, next_db_idx))
                next_db_idx += 1

            # in any case, we proceed with the next bestlist record.
            curr_bl_idx += 1

        return insertion_mask, deletion_mask, similar_records

    def _get_record_similarity(self, record1: np.record, record2: np.record) -> int:
        """
        Compares two records and computes their similarity relation.

        :param record1: the first record.
        :param record2: the record, against which the first record is compared.
        :return: +1 whenever they are considered equal, 0 if there are only differences not related to the result and
        -1 whenever they are differ in the result.
        """
        result_equal = self._compare_record_fields(record1, record2, fields=[
            BestlistField.RESULT,
            BestlistField.RANK,
            BestlistField.LOCATION,
            BestlistField.DATE,
            BestlistField.ATHLETE_CODE,
            BestlistField.CLUB_CODE,
            BestlistField.EVENT_CODE
        ])
        if self.wind_relevant:
            both_nan = np.isnan(record1[BestlistField.WIND.value]) and np.isnan(record2[BestlistField.WIND.value])
            if not both_nan:
                if np.isnan(record1[BestlistField.WIND.value]) or np.isnan(record2[BestlistField.WIND.value]):
                    return -1
                result_equal &= int(record1[BestlistField.WIND.value] * 10) == int(record2[BestlistField.WIND.value] * 10)
        if self.homologation_relevant:
            result_equal &= record1[BestlistField.NOT_HOMOLOGATED.value] == record2[BestlistField.NOT_HOMOLOGATED.value]
        if not result_equal:
            return -1

        return 1 if self._compare_record_fields(record1, record2, fields=[
            BestlistField.ATHLETE,
            BestlistField.NATIONALITY,
            BestlistField.BIRTHDATE,
            BestlistField.CLUB,
            BestlistField.EVENT
        ]) else 0

    @staticmethod
    def _update_entries(athlete: Athlete, club: Club, event: Event, record: np.record) -> int:
        """
        Update database entries (athlete, club and event) according to a record from the bestlist.
        We only update an entry, if the bestlist result date is later or equal to the latest date associated
        with the entry. We only increase the update count with changes to fields that are present in the bestlist.

        :param athlete: the athlete associated with the corresponding database record.
        :param club: the club associated with the corresponding database record.
        :param event: the event associated with the corresponding database record.
        :param record: the record which forms the source of truth for the record.
        :return: the total number of performed updates.
        """
        result_date = record[BestlistField.DATE.value].item()
        amount_updates = 0
        if result_date >= athlete.latest_date:
            if athlete.name != record[BestlistField.ATHLETE.value]:
                athlete.name = record[BestlistField.ATHLETE.value]
                amount_updates += 1
            if athlete.birthdate != record[BestlistField.BIRTHDATE.value].item():
                athlete.birthdate = record[BestlistField.BIRTHDATE.value].item()
                amount_updates += 1
            if athlete.nationality != record[BestlistField.NATIONALITY.value]:
                athlete.nationality = record[BestlistField.NATIONALITY.value]
                amount_updates += 1
            athlete.latest_date = result_date

        if result_date >= club.latest_date:
            if club.name != record[BestlistField.CLUB.value]:
                club.name = record[BestlistField.CLUB.value]
                amount_updates += 1
            club.latest_date = result_date

        if result_date >= event.latest_date:
            if event.name != record[BestlistField.EVENT.value]:
                event.name = record[BestlistField.EVENT.value]
                amount_updates += 1
            event.latest_date = result_date

        return amount_updates

    @staticmethod
    def _compare_record_fields(record1: np.record, record2: np.record, fields: [BestlistField]) -> bool:
        """
        Checks whether the given records are equal regarding the values of several fields.

        :param record1: the first record.
        :param record2: the second record.
        :param fields: the fields, which are used for comparison.
        :return: whether the records are equal.
        """
        return all([record1[field.value] == record2[field.value] for field in fields])

    def _read_results_from_database(self, discipline: Discipline) -> np.recarray:
        """
        Reads the results from the database by transforming them to a heterogeneous record array.

        :param discipline: the discipline from which the results are fetched.
        :return: array of records.
        """
        with DatabaseConnection(self.config) as database:
            # ignoring the category (only a problem if we fetch other category than 'M' or 'F'.
            results: list[Result] = database.session.query(Result).filter(
                Result.discipline_id == discipline.id,
                sqlalchemy.extract("year", Result.date) == self.scrape_config.year,
                Result.manual.is_(False),
                Result.homologated if not self.scrape_config.allow_nonhomologated else True,
                Result.wind <= 2.0 if Result.wind and not self.scrape_config.allow_wind else True,
            ).order_by(
                Result.performance.asc() if discipline.config.ascending else Result.performance.desc(),
                Result.date.asc()
            ).limit(self.scrape_config.amount).all()

            if len(results) == self.scrape_config.amount:
                # This can have bad implications. E.g., the deletion of results that are (now) out of scope
                logger.warning(f"Reached limit fetching results from database. Limit: {self.scrape_config.amount}.")

            return self._results_to_records(results)

    @staticmethod
    def _results_to_records(results: list[Result]) -> np.recarray:
        """
        Transforms the database results to a record array.

        :param results: the results from the database.
        :return: heterogeneous array of records.
        """
        dtypes = np.dtype(
            [
                BestlistField.ID.get_dtype_pair(),
                BestlistField.RESULT.get_dtype_pair(),
                BestlistField.WIND.get_dtype_pair(),
                BestlistField.RANK.get_dtype_pair(),
                BestlistField.NOT_HOMOLOGATED.get_dtype_pair(),
                BestlistField.ATHLETE.get_dtype_pair(),
                BestlistField.CLUB.get_dtype_pair(),
                BestlistField.NATIONALITY.get_dtype_pair(),
                BestlistField.BIRTHDATE.get_dtype_pair(),
                BestlistField.EVENT.get_dtype_pair(),
                BestlistField.LOCATION.get_dtype_pair(),
                BestlistField.DATE.get_dtype_pair(),
                BestlistField.ATHLETE_CODE.get_dtype_pair(),
                BestlistField.CLUB_CODE.get_dtype_pair(),
                BestlistField.EVENT_CODE.get_dtype_pair()
            ]
        )

        data = np.empty(len(results), dtype=dtypes)
        for idx, result in enumerate(results):
            data[idx] = (
                result.id,
                result.performance,
                np.nan if result.wind is None else result.wind,
                result.rank or "",
                not result.homologated,
                result.athlete.name,
                result.club.name,
                result.athlete.nationality,
                result.athlete.birthdate,
                result.event.name,
                result.location,
                result.date,
                result.athlete.athlete_code,
                result.club.club_code,
                result.event.event_code
            )

        return data.view(np.recarray)

    @staticmethod
    def _sanity_check_results(bestlist: pd.DataFrame, ascending: bool) -> bool:
        """
        Sanity checks the parsed results of the bestlist.

        :param bestlist: the bestlist.
        :param ascending: whether the results must be in ascending order.
        :return: whether the results are getting monotonically better.
        """
        return bestlist[BestlistField.RESULT.value].is_monotonic_decreasing if not ascending \
            else bestlist[BestlistField.RESULT.value].is_monotonic_increasing

    @staticmethod
    def _parse_result(serialized_result: str) -> int:
        """
        Parses a serialized result.

        :param serialized_result: the serialized time/distance/height.
        :return: integer representing the result. -1 if not parsable (invalid).
        """
        # since we have some results of the form: xx:xx.xx_SR_U18\nResultat wurde [...]
        serialized_result = serialized_result.split("\n")[0].split("_")[0]

        # see: https://pythex.org/ by removing all escape symbols ('\')
        # matches everything of the form HH:mm:ss.hh (ss < 60) or ss.hh (with ss >= 60)
        match = re.match('^(?:(?:(\\d+):)?([0-5]?\\d):)?([0-5]?\\d)(?:\\.(\\d{1,2}))?$', serialized_result) \
                or re.match('^(\\d+):([0-5]?\\d)(?:\\.(\\d{1,2}))?$', serialized_result) \
                or re.match('^(\\d+)(?:\\.(\\d{1,2}))?$', serialized_result)

        if not match:
            return -1

        groups = match.groups()
        if len(groups) == 3:
            groups = (None, *groups)
        if len(groups) == 2:
            groups = (None, None, *groups)

        hours, minutes, seconds, hundreds = groups
        total = int(hundreds.ljust(2, '0')) if hundreds else 0
        total += int(seconds) * SECONDS_TO_HUNDREDTHS
        total += int(minutes) * MINUTES_TO_HUNDREDTHS if minutes else 0
        total += int(hours) * HOURS_TO_HUNDREDTHS if hours else 0

        return total
