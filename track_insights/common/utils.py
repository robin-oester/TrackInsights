import pathlib
from typing import Optional

import yaml
from jsonschema import validate
from jsonschema.exceptions import ValidationError


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
