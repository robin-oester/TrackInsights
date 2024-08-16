from track_insights.scraping import BestlistCategory


def test_get_junior_categories():
    expected_men = [
        BestlistCategory.U_10_M,
        BestlistCategory.U_12_M,
        BestlistCategory.U_14_M,
        BestlistCategory.U_16_M,
        BestlistCategory.U_18_M,
        BestlistCategory.U_20_M,
    ]
    result_men = BestlistCategory.get_junior_categories(male=True)

    assert result_men == expected_men

    expected_women = [
        BestlistCategory.U_10_W,
        BestlistCategory.U_12_W,
        BestlistCategory.U_14_W,
        BestlistCategory.U_16_W,
        BestlistCategory.U_18_W,
        BestlistCategory.U_20_W,
    ]
    result_women = BestlistCategory.get_junior_categories(male=False)

    assert result_women == expected_women


def test_get_age_bounds():
    lower_bound, upper_bound = BestlistCategory.get_age_bounds(BestlistCategory.U_10_M)
    assert lower_bound == 0
    assert upper_bound == 10

    lower_bound, upper_bound = BestlistCategory.get_age_bounds(BestlistCategory.U_12_W)
    assert lower_bound == 10
    assert upper_bound == 12

    lower_bound, upper_bound = BestlistCategory.get_age_bounds(BestlistCategory.U_14_M)
    assert lower_bound == 12
    assert upper_bound == 14

    lower_bound, upper_bound = BestlistCategory.get_age_bounds(BestlistCategory.U_16_W)
    assert lower_bound == 14
    assert upper_bound == 16

    lower_bound, upper_bound = BestlistCategory.get_age_bounds(BestlistCategory.U_18_M)
    assert lower_bound == 16
    assert upper_bound == 18

    lower_bound, upper_bound = BestlistCategory.get_age_bounds(BestlistCategory.U_20_W)
    assert lower_bound == 18
    assert upper_bound == 20

    lower_bound, upper_bound = BestlistCategory.get_age_bounds(BestlistCategory.MEN)
    assert lower_bound == 20
    assert upper_bound == 200

    lower_bound, upper_bound = BestlistCategory.get_age_bounds(BestlistCategory.ALL_WOMEN)
    assert lower_bound == 0
    assert upper_bound == 200
