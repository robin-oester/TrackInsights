import os
import pathlib
import re
import time
from datetime import date, datetime
from typing import Optional

import yaml
from jsonschema import validate
from jsonschema.exceptions import ValidationError

CONFIG_SCHEMA_PATH = (
    pathlib.Path(os.path.abspath(__file__)).parent.parent / "config" / "schema" / "configuration_schema.yaml"
)
CONFIG_PATH = pathlib.Path(os.path.abspath(__file__)).parent.parent / "config" / "configuration.yaml"
IGNORED_PATH = pathlib.Path(os.path.abspath(__file__)).parent.parent / "config" / "ignored_entries.json"

ANOMALIES_PATH = pathlib.Path(os.path.abspath(__file__)).parent.parent / "anomalies"

DATE_FORMAT = "%d.%m.%Y"

HOURS_TO_HUNDREDTHS = 100 * 60 * 60
MINUTES_TO_HUNDREDTHS = 100 * 60
SECONDS_TO_HUNDREDTHS = 100


def validate_yaml(concrete_file: dict, schema_path: pathlib.Path) -> tuple[bool, Optional[ValidationError]]:
    """
    Validates a yaml file against a schema.

    :param concrete_file: the loaded content of the file.
    :param schema_path: path to the schema.
    :return: whether the file is valid and if not, the corresponding error.
    """
    assert schema_path.is_file(), f"Schema file does not exist: {schema_path}"

    with open(schema_path, "r", encoding="utf-8") as schema_file:
        schema = yaml.safe_load(schema_file)

    try:
        validate(concrete_file, schema)
    except ValidationError as error:
        return False, error

    return True, None


def current_time_millis() -> int:
    timestamp = time.time() * 1000
    return int(round(timestamp))


def parse_date(serialized_date: str) -> Optional[date]:
    try:
        # Attempt to parse the string with the specified format
        parsed_date = datetime.strptime(serialized_date, DATE_FORMAT).date()
        return parsed_date  # Successfully parsed
    except ValueError:
        # Parsing failed due to incorrect format
        return None


def parse_result(serialized_result: str) -> int:
    """
    Parses a serialized result.

    :param serialized_result: the serialized time/distance/height.
    :return: integer representing the result. -1 if not parsable (invalid).
    """

    # since we have some results of the form: xx:xx.xx_SR_U18\nResultat wurde [...]
    serialized_result = serialized_result.split("\n")[0].split("_")[0]
    # serialized_result = re.sub("[^(0-9.:)]", "", serialized_result)

    # see: https://pythex.org/ by removing all escape symbols ('\')
    # matches everything of the form HH:mm:ss.hh (ss < 60) or ss.hh (with ss >= 60)
    match = (
        re.match("^(?:(?:(\\d+):)?([0-5]?\\d):)?([0-5]?\\d)(?:\\.(\\d{1,2}))?$", serialized_result)
        or re.match("^(\\d+):([0-5]?\\d)(?:\\.(\\d{1,2}))?$", serialized_result)
        or re.match("^(\\d+)(?:\\.(\\d{1,2}))?$", serialized_result)
    )

    if not match:
        return -1

    groups = match.groups()
    if len(groups) == 3:
        groups = (None, *groups)
    if len(groups) == 2:
        groups = (None, None, *groups)

    hours, minutes, seconds, hundreds = groups
    total = int(hundreds.ljust(2, "0")) if hundreds else 0
    total += int(seconds) * SECONDS_TO_HUNDREDTHS
    total += int(minutes) * MINUTES_TO_HUNDREDTHS if minutes else 0
    total += int(hours) * HOURS_TO_HUNDREDTHS if hours else 0

    return total


def parse_float(serialized_value: str) -> Optional[float]:
    if serialized_value == "":
        return None
    try:
        # Try to convert the string to a float
        number = float(serialized_value)
        return number
    except ValueError:
        return float("nan")
