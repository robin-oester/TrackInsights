from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from track_insights.database.models import Discipline, DisciplineConfiguration
from track_insights.scores import NO_RESULT_SENTINEL, ScoreList


def get_sample_discipline(ascending: bool = True) -> Discipline:
    config = DisciplineConfiguration(
        id=1,
        name="100 m" if ascending else "Long Jump",
        ascending=ascending,
    )
    return Discipline(
        id=1,
        config_id=1,
        discipline_code="Test_Code",
        indoor=False,
        male=True,
        score_identifier="100m" if ascending else "LJ",
        config=config,
    )


@patch("track_insights.scores.score_list.STORE_FOLDER", Path("/sample/store"))
def test_init_error():
    discipline = MagicMock()
    discipline.score_identifier = "test_score"
    discipline.indoor = False
    discipline.male = True

    expected_path = Path("/sample/store/outdoor/men/test_score.npy")

    with patch.object(Path, "is_file", return_value=False) as is_file_mock:
        with pytest.raises(FileNotFoundError) as exc_info:
            ScoreList(discipline)

        exception_message = str(exc_info.value)

        assert str(expected_path) in exception_message
        is_file_mock.assert_called_once()


# pylint: disable=too-many-statements
@patch.object(Path, "is_file", return_value=True)
def test_init(is_file_mock: MagicMock):
    arr = np.zeros(1400)

    with patch("numpy.load", return_value=arr):
        discipline = get_sample_discipline(True)
        score_list = ScoreList(discipline)

        assert score_list.worst == 0
        assert score_list.best == 0
        assert score_list.arr.shape == (1400,)
        assert score_list.ascending

    arr = np.arange(1, 1401)
    with patch("numpy.load", return_value=arr):
        discipline = get_sample_discipline(True)
        score_list = ScoreList(discipline)

        assert score_list.worst == 1400
        assert score_list.best == 1
        assert score_list.arr.shape == (1400,)
        assert score_list.ascending

    arr = np.arange(1400, 0, -1)
    with patch("numpy.load", return_value=arr):
        discipline = get_sample_discipline(False)
        score_list = ScoreList(discipline)

        assert score_list.worst == 1
        assert score_list.best == 1400
        assert score_list.arr.shape == (1400,)
        assert not score_list.ascending

    arr = np.arange(1400, 0, -1)
    arr[0] = NO_RESULT_SENTINEL
    arr[1] = NO_RESULT_SENTINEL
    arr[3] = NO_RESULT_SENTINEL
    arr[1398] = NO_RESULT_SENTINEL
    arr[1399] = NO_RESULT_SENTINEL
    with patch("numpy.load", return_value=arr):
        discipline = get_sample_discipline(False)
        score_list = ScoreList(discipline)

        assert score_list.worst == 3
        assert score_list.best == 1398
        assert score_list.arr.shape == (1400,)
        assert not score_list.ascending

    arr = np.arange(1, 1401)
    arr[0] = NO_RESULT_SENTINEL
    arr[1] = NO_RESULT_SENTINEL

    for i in range(2, 1398):
        if i % 2 == 0:
            arr[i] = NO_RESULT_SENTINEL

    arr[1398] = NO_RESULT_SENTINEL
    arr[1399] = NO_RESULT_SENTINEL

    expected_arr = np.arange(1, 1401)
    expected_arr[0] = 0
    expected_arr[1] = 0
    expected_arr[2] = 0
    expected_arr[1398] = 1398
    expected_arr[1399] = 1398

    for i in range(4, 1398):
        if i % 2 == 0:
            expected_arr[i] = i

    with patch("numpy.load", return_value=arr):
        discipline = get_sample_discipline(True)
        score_list = ScoreList(discipline)

        assert score_list.worst == 1398
        assert score_list.best == 4
        assert score_list.arr.tolist() == expected_arr.tolist()
        assert score_list.arr.shape == (1400,)
        assert score_list.ascending
    assert is_file_mock.call_count == 5


@patch.object(Path, "is_file", return_value=True)
def test_find_score(is_file_mock: MagicMock):
    arr = np.arange(1, 1401)
    arr[0] = NO_RESULT_SENTINEL
    arr[800] = NO_RESULT_SENTINEL
    arr[1399] = NO_RESULT_SENTINEL

    with patch("numpy.load", return_value=arr):
        discipline = get_sample_discipline(True)
        score_list = ScoreList(discipline)

        assert score_list.find_score(1) == -1
        assert score_list.find_score(2) == 1399
        assert score_list.find_score(1399) == 2
        assert score_list.find_score(1400) == 0
        assert score_list.find_score(600) == 1400 - 600 + 1
        assert score_list.find_score(801) == 1400 - 802 + 1

    arr = np.arange(1400, 0, -1)
    arr[0] = NO_RESULT_SENTINEL
    arr[800] = NO_RESULT_SENTINEL
    arr[1399] = NO_RESULT_SENTINEL

    with patch("numpy.load", return_value=arr):
        discipline = get_sample_discipline(False)
        score_list = ScoreList(discipline)

        assert score_list.best == 1399
        assert score_list.worst == 2

        assert score_list.find_score(1400) == -1
        assert score_list.find_score(1399) == 1399
        assert score_list.find_score(2) == 2
        assert score_list.find_score(1) == 0
        assert score_list.find_score(600) == 599
        assert score_list.find_score(801) == 801

    assert is_file_mock.call_count == 2


@patch.object(Path, "is_file", return_value=True)
def test_performance(is_file_mock: MagicMock):
    arr = np.arange(1400, 0, -1)
    arr[0] = NO_RESULT_SENTINEL
    arr[600] = NO_RESULT_SENTINEL
    arr[1399] = NO_RESULT_SENTINEL

    with patch("numpy.load", return_value=arr):
        discipline = get_sample_discipline(False)
        score_list = ScoreList(discipline)

        assert score_list.best == 1399
        assert score_list.worst == 2
        assert score_list.find_performance(1400) is None
        assert score_list.find_performance(1399) == 1399
        assert score_list.find_performance(1398) == 1398
        assert score_list.find_performance(800) == 801
        assert score_list.find_performance(1) == 2

    assert is_file_mock.call_count == 1
