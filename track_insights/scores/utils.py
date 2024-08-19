import os
import pathlib

STORE_FOLDER = pathlib.Path(os.path.abspath(__file__)).parent / "lists"
RAW_DATA_FOLDER = pathlib.Path(os.path.abspath(__file__)).parent / "data"

POINTS_IDENTIFIER = "Points"
MAX_POINTS = 1400
NO_RESULT_SENTINEL = -2
