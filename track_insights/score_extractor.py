import argparse
import logging
import pathlib

import numpy as np
import pandas as pd
import tabula
import yaml
from tqdm import tqdm
from track_insights.common import CONFIG_PATH, CONFIG_SCHEMA_PATH, parse_result, read_json_file, validate_json
from track_insights.scores import MAX_POINTS, NO_RESULT_SENTINEL, POINTS_IDENTIFIER, RAW_DATA_FOLDER, STORE_FOLDER

logging.basicConfig(
    level=logging.NOTSET,
    format="[%(asctime)s]  [%(filename)15s:%(lineno)4d] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
)
logger = logging.getLogger(__name__)


# pylint: disable=too-many-statements,too-many-branches
def main() -> None:
    """
    Main function to update the score tables for the TrackInsights application.
    """

    parser = argparse.ArgumentParser(description="TrackInsights - Scoring Calculation")

    parser.add_argument("--indoor", action="store_true", help="Update tables for indoor events.")
    parser.add_argument("--outdoor", action="store_true", help="Update tables for outdoor events.")
    parser.add_argument("--combined", action="store_true", help="Validate the combined events.")
    parser.add_argument("--male", action="store_true", help="Update tables for male athletes.")
    parser.add_argument("--female", action="store_true", help="Update tables for female athletes.")

    logger.info("Checking configuration file...")
    logging.getLogger("tabula").setLevel(logging.ERROR)
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config: dict = yaml.safe_load(config_file)
    if not check_configuration(config, CONFIG_SCHEMA_PATH):
        return

    args = parser.parse_args()

    combined = args.combined if args.outdoor or args.indoor else True
    outdoor = args.outdoor if args.combined or args.indoor else True
    indoor = args.indoor if args.combined or args.outdoor else True
    male = args.male if args.male ^ args.female else True
    female = args.female if args.male ^ args.female else True

    if combined:
        loaded_json = read_json_file(RAW_DATA_FOLDER / config["score_lists"]["combined"]["file"])
        if not check_configuration(loaded_json, RAW_DATA_FOLDER / config["score_lists"]["combined"]["schema"]):
            return
        logger.info("Validated file for combined events.")

    if outdoor:
        logger.info("Updating tables for outdoor events.")
        read_path = RAW_DATA_FOLDER / config["score_lists"]["outdoor"]["file"]

        if male:
            table_ranges = config["score_lists"]["outdoor"]["men"]
            write_path = STORE_FOLDER / "outdoor" / "men"
            write_path.mkdir(parents=True, exist_ok=True)

            with tqdm(table_ranges, desc="Extracting outdoor/male", unit="table range") as manager:
                for table_range in manager:
                    read_tables(read_path, write_path, table_range)

            logger.info("Successfully wrote male events.")
        if female:
            table_ranges = config["score_lists"]["outdoor"]["women"]
            write_path = STORE_FOLDER / "outdoor" / "women"
            write_path.mkdir(parents=True, exist_ok=True)

            with tqdm(table_ranges, desc="Extracting outdoor/female", unit="table range") as manager:
                for table_range in manager:
                    read_tables(read_path, write_path, table_range)
            logger.info("Successfully wrote female events.")

    if indoor:
        logger.info("Updating tables for indoor events.")
        read_path = RAW_DATA_FOLDER / config["score_lists"]["indoor"]["file"]

        if male:
            table_ranges = config["score_lists"]["indoor"]["men"]
            write_path = STORE_FOLDER / "indoor" / "men"
            write_path.mkdir(parents=True, exist_ok=True)

            with tqdm(table_ranges, desc="Extracting indoor/male", unit="table range") as manager:
                for table_range in manager:
                    read_tables(read_path, write_path, table_range)

            logger.info("Successfully wrote male events.")
        if female:
            table_ranges = config["score_lists"]["indoor"]["women"]
            write_path = STORE_FOLDER / "indoor" / "women"
            write_path.mkdir(parents=True, exist_ok=True)

            with tqdm(table_ranges, desc="Extracting indoor/female", unit="table range") as manager:
                for table_range in manager:
                    read_tables(read_path, write_path, table_range)
            logger.info("Successfully wrote female events.")


def check_configuration(config: dict, schema_path: pathlib.Path) -> bool:
    valid_yaml, exception = validate_json(config, schema_path)

    if not valid_yaml:
        logger.error(f"Error while validating configuration file for schema-compliance: {exception.message}")
        logger.error(exception)
        return False
    return True


def read_tables(file: pathlib.Path, store_folder: pathlib.Path, table_range: str) -> None:
    """
    Read the tables from the specified pdf file and the given range. Then, the resulting performance tables
    are stored to the given folder. Raises a ValueError if no tables are found in the given range, if the number
    of rows is not equal to the expected number of rows, or if at least one entry cannot be parsed.

    :param file: The path to the pdf file.
    :param store_folder: The folder to store the resulting tables.
    :param table_range: The range of tables to extract.
    """

    tables = tabula.read_pdf(file, pages=table_range, multiple_tables=True)

    if not tables:
        raise ValueError("No tables were found in the specified page range of the PDF.")

    reference_columns = tables[0].columns.tolist()

    standardized_tables = []
    for table in tables:
        table = table.reindex(columns=reference_columns)
        standardized_tables.append(table.astype(str))

    merged_df = pd.concat(standardized_tables, ignore_index=True)

    num_rows = merged_df.shape[0]

    if num_rows != MAX_POINTS:
        raise ValueError(f"Expected {MAX_POINTS} rows, but got {num_rows}.")
    merged_df = merged_df.drop(columns=[POINTS_IDENTIFIER])
    merged_df = merged_df.map(lambda x: parse_result(x) if x != "-" else NO_RESULT_SENTINEL)

    if (merged_df == -1).any().any():
        raise ValueError("At least one entry of the dataframe cannot be parsed.")

    for column in merged_df.columns:
        array = merged_df[column].values
        output_path = store_folder / f"{column}.npy"
        np.save(output_path, array)


if __name__ == "__main__":
    main()
