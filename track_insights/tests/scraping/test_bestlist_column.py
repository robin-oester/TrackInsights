from track_insights.scraping import BestlistColumn


def test_get_column():
    assert BestlistColumn.get_column("Nr") == BestlistColumn.NUMBER
    assert BestlistColumn.get_column("Name") == BestlistColumn.ATHLETE
    assert BestlistColumn.get_column("Verein") == BestlistColumn.CLUB
    assert BestlistColumn.get_column("Wettkampf") == BestlistColumn.EVENT
    assert BestlistColumn.get_column("Resultat") == BestlistColumn.RESULT
    assert BestlistColumn.get_column("Wind") == BestlistColumn.WIND
    assert BestlistColumn.get_column("Rang") == BestlistColumn.RANK
    assert BestlistColumn.get_column("NH*") == BestlistColumn.NOT_HOMOLOGATED
    assert BestlistColumn.get_column("Nat.") == BestlistColumn.NATIONALITY
    assert BestlistColumn.get_column("Geb. Dat.") == BestlistColumn.BIRTHDATE
    assert BestlistColumn.get_column("Ort") == BestlistColumn.LOCATION
    assert BestlistColumn.get_column("Datum") == BestlistColumn.DATE
    assert BestlistColumn.get_column("athlete_code") == BestlistColumn.ATHLETE_CODE
    assert BestlistColumn.get_column("club_code") == BestlistColumn.CLUB_CODE
    assert BestlistColumn.get_column("event_code") == BestlistColumn.EVENT_CODE
    assert BestlistColumn.get_column("id") == BestlistColumn.ID
    assert BestlistColumn.get_column("Verein / Schule / Ort") == BestlistColumn.CLUB

    assert BestlistColumn.get_column("Not a column") is None
