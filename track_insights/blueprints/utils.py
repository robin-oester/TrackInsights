from typing import Optional


def str_to_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in ("true", "1")


def str_to_category(value: Optional[str]) -> tuple[str, bool]:
    if value is None:
        return "all", True
    splitted_val = value.split("_")
    if len(splitted_val) == 1:
        return ("men", True) if splitted_val[0] == "m" else ("women", False)
    return splitted_val[0], splitted_val[1] == "m"


# pylint: disable=too-many-return-statements
def get_age_bounds(category: str, restrict_category: bool) -> tuple[int, int]:
    if category.lower() == "masters":
        return 30, 200
    if category.lower() == "men" or category.lower() == "women":
        return (20, 30) if restrict_category else (20, 200)
    if category.lower() == "u23":
        return (20, 23) if restrict_category else (0, 23)
    if category.lower() == "u20":
        return (18, 20) if restrict_category else (0, 20)
    if category.lower() == "u18":
        return (16, 18) if restrict_category else (0, 18)
    if category.lower() == "u16":
        return (14, 16) if restrict_category else (0, 16)
    if category.lower() == "u14":
        return (12, 14) if restrict_category else (0, 14)
    if category.lower() == "u12":
        return (10, 12) if restrict_category else (0, 12)
    if category.lower() == "u10":
        return (0, 10) if restrict_category else (0, 10)
    return 0, 200
