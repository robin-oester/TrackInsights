import sys
from typing import Optional

import numpy as np
from track_insights.common.utils import INVALID_RESULT_SENTINEL
from track_insights.database.models import Discipline
from track_insights.scores.utils import MAX_POINTS, STORE_FOLDER


class ScoreList:
    """
    A class to represent a list of performance scores for a discipline.
    """

    def __init__(self, discipline: Discipline) -> None:
        assert discipline.score_identifier is not None

        place = "indoor" if discipline.indoor else "outdoor"
        gender = "men" if discipline.male else "women"
        full_path = STORE_FOLDER / place / gender / f"{discipline.score_identifier}.npy"

        if not full_path.is_file():
            raise FileNotFoundError(f"{full_path} was not found.")

        loaded_arr: np.ndarray = np.load(full_path)

        assert loaded_arr.shape == (MAX_POINTS,)

        self.ascending = discipline.config.ascending

        curr_idx = 0
        fill_invalid_val = 0 if self.ascending else sys.maxsize
        while curr_idx < loaded_arr.size and loaded_arr[curr_idx] == -2:
            loaded_arr[curr_idx] = fill_invalid_val
            curr_idx += 1

        last_val = loaded_arr[curr_idx] if curr_idx < loaded_arr.size else fill_invalid_val
        self.best: int = last_val  # type: ignore

        for i in range(curr_idx + 1, loaded_arr.size):
            curr_val = loaded_arr[i]
            if curr_val != -2:
                last_val = loaded_arr[i]
            else:
                loaded_arr[i] = last_val
        self.worst: int = last_val  # type: ignore
        self.arr = loaded_arr

        if self.ascending:
            assert np.all(self.arr[:-1] <= self.arr[1:])
        else:
            assert np.all(self.arr[:-1] >= self.arr[1:])

    def find_score(self, performance: int) -> int:
        """
        Find the score for a given performance.

        :param performance: The performance to find the score for.
        :return: The score for the given performance or INVALID_RESULT_SENTINEL if better than the best possible score.
        """
        if (self.ascending and (performance < self.best)) or (not self.ascending and (performance > self.best)):
            return INVALID_RESULT_SENTINEL
        if (self.ascending and (performance > self.worst)) or (not self.ascending and (performance < self.worst)):
            return 0

        # here: performance is between best and worst (i.e., in table range)
        if self.ascending:
            return MAX_POINTS - np.searchsorted(self.arr, performance, side="left")
        return MAX_POINTS - np.searchsorted(-self.arr, -performance, side="left")

    def find_performance(self, score: int) -> Optional[int]:
        """
        Find the performance for a given score. The returned performance gives a lower bound for the score.
        Returns None if the performance is better than self.best.

        :param score: The score to find the performance for.
        :return: The performance for the given score.
        """

        assert 1 <= score <= MAX_POINTS

        fetched_perf = self.arr[MAX_POINTS - score].item()
        ret_val: Optional[int] = None

        if (fetched_perf == 0 and self.ascending) or (fetched_perf == sys.maxsize and not self.ascending):
            return ret_val

        return fetched_perf
