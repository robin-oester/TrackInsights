from enum import Enum
from typing import Any
import numpy as np


class BestlistField(Enum):
    NUMBER = ("Nr", np.int64)
    ATHLETE = ("Name", np.object_)
    CLUB = ("Verein", np.object_)
    EVENT = ("Wettkampf", np.object_)
    RESULT = ("Resultat", np.int64)
    WIND = ("Wind", np.float64)
    RANK = ("Rang", np.object_)
    NOT_HOMOLOGATED = ("NH*", np.bool_)
    NATIONALITY = ("Nat.", np.object_)
    BIRTHDATE = ("Geb. Dat.", np.dtype("datetime64[D]"))
    LOCATION = ("Ort", np.object_)
    DATE = ("Datum", np.dtype("datetime64[D]"))
    ATHLETE_CODE = ("athlete_code", np.object_)
    CLUB_CODE = ("club_code", np.object_)
    EVENT_CODE = ("event_code", np.object_)
    SCRAPE_CONFIG = ("scrape_config", np.object_)
    ID = ("id", np.int64)
    VALID = ("valid", np.bool_)

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    # ignore the first param since it's already set by __new__
    def __init__(self, _: str, dtype: Any, *args, **kwds):
        super().__init__(*args, **kwds)
        self._dtype_ = dtype

    def __str__(self):
        return self.value

    @property
    def dtype(self):
        return self._dtype_

    def get_dtype_pair(self) -> (str, Any):
        return self.value, self.dtype

    @staticmethod
    def get_mapping() -> dict[str, Any]:
        return {field.value: field.dtype for field in BestlistField}
