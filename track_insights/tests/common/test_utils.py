from track_insights.common.utils import parse_result


def test_parse_result():
    assert parse_result("6.21") == 621
    assert parse_result("8") == 800
    assert parse_result("15.93") == 1593
    assert parse_result("27.3") == 2730
    assert parse_result("63.81") == 6381
    assert parse_result("82.99") == 8299
    assert parse_result("102.1") == 10210
    assert parse_result("5103") == 510300
    assert parse_result("10931") == 1093100

    assert parse_result("0:09.14") == 914
    assert parse_result("0:45.4") == 4540
    assert parse_result("0:59.64") == 5964
    assert parse_result("1:00.23") == 6023
    assert parse_result("01:35.5") == 9550
    assert parse_result("2:04.39") == 12439
    assert parse_result("12:49.48") == 76948
    assert parse_result("27:36.2") == 165620
    assert parse_result("63:12.3") == 379230

    assert parse_result("1:05:15.10") == 391510
    assert parse_result("01:28:49.6") == 532960
    assert parse_result("25:58:32") == 9351200

    assert parse_result("10.23_SR_U23") == 1023
    assert parse_result("1:02.48_SB\nWind") == 6248

    assert parse_result("1:62.9") == -1
    assert parse_result("83.48.12") == -1
    assert parse_result("25:12:54:31") == -1
    assert parse_result("10.4a") == 1040
