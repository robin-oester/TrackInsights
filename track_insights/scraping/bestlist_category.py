from enum import StrEnum  # type: ignore[attr-defined]


class BestlistCategory(StrEnum):
    """
    Holds all categories that are available to the system. The values represent the code for each category used in the
    URL.
    """

    U_10_M = ("5c4o3k5m-d686mo-j986g2ie-1-j986g45f-be",)
    U_10_W = ("5c4o3k5m-d686mo-j986g2ie-1-j986g45i-bf",)
    U_12_M = ("5c4o3k5m-d686mo-j986g2ie-1-j986g45k-bg",)
    U_12_W = ("5c4o3k5m-d686mo-j986g2ie-1-j986g45m-bh",)
    U_14_M = ("5c4o3k5m-d686mo-j986g2ie-1-j986g45o-bi",)
    U_14_W = ("5c4o3k5m-d686mo-j986g2ie-1-j986g45q-bj",)
    U_16_M = ("5c4o3k5m-d686mo-j986g2ie-1-j986g45s-bk",)
    U_16_W = ("5c4o3k5m-d686mo-j986g2ie-1-j986g45u-bl",)
    U_18_M = ("5c4o3k5m-d686mo-j986g2ie-1-j986g45w-bm",)
    U_18_W = ("5c4o3k5m-d686mo-j986g2ie-1-j986g45y-bn",)
    U_20_M = ("5c4o3k5m-d686mo-j986g2ie-1-j986g45z-bo",)
    U_20_W = ("5c4o3k5m-d686mo-j986g2ie-1-j986g461-bp",)
    MEN = ("5c4o3k5m-d686mo-j986g2ie-1-j986g467-bs",)
    WOMEN = ("5c4o3k5m-d686mo-j986g2ie-1-j986g469-bt",)
    ALL_MEN = ("M",)
    ALL_WOMEN = "W"

    @staticmethod
    def get_junior_categories(male: bool) -> list["BestlistCategory"]:
        """
        Get all categories that belong to juniors.

        :param male: whether to consider male athletes
        :return: set of all junior categories.
        """

        if male:
            return [
                BestlistCategory.U_10_M,  # type: ignore[list-item]
                BestlistCategory.U_12_M,  # type: ignore[list-item]
                BestlistCategory.U_14_M,  # type: ignore[list-item]
                BestlistCategory.U_16_M,  # type: ignore[list-item]
                BestlistCategory.U_18_M,  # type: ignore[list-item]
                BestlistCategory.U_20_M,  # type: ignore[list-item]
            ]
        return [
            BestlistCategory.U_10_W,  # type: ignore[list-item]
            BestlistCategory.U_12_W,  # type: ignore[list-item]
            BestlistCategory.U_14_W,  # type: ignore[list-item]
            BestlistCategory.U_16_W,  # type: ignore[list-item]
            BestlistCategory.U_18_W,  # type: ignore[list-item]
            BestlistCategory.U_20_W,  # type: ignore[list-item]
        ]

    @staticmethod
    def get_age_bounds(category: "BestlistCategory") -> tuple[int, int]:
        """
        Compute the age bounds of a particular category.

        :param category: the category from which the bounds are taken.
        :return: (lower bound, upper bound) tuple.
        """

        lower_bound = 0
        upper_bound = 200

        if category in {BestlistCategory.U_10_M, BestlistCategory.U_10_W}:
            upper_bound = 10
        elif category in {BestlistCategory.U_12_M, BestlistCategory.U_12_W}:
            lower_bound = 10
            upper_bound = 12
        elif category in {BestlistCategory.U_14_M, BestlistCategory.U_14_W}:
            lower_bound = 12
            upper_bound = 14
        elif category in {BestlistCategory.U_16_M, BestlistCategory.U_16_W}:
            lower_bound = 14
            upper_bound = 16
        elif category in {BestlistCategory.U_18_M, BestlistCategory.U_18_W}:
            lower_bound = 16
            upper_bound = 18
        elif category in {BestlistCategory.U_20_M, BestlistCategory.U_20_W}:
            lower_bound = 18
            upper_bound = 20
        elif category in {BestlistCategory.MEN, BestlistCategory.WOMEN}:
            lower_bound = 20

        return lower_bound, upper_bound
