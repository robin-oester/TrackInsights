from typing import Any, Optional

import sqlalchemy
from flask import Blueprint, Response, current_app, jsonify, request
from sqlalchemy import and_, func, or_
from track_insights.blueprints.utils import get_age_bounds, str_to_bool, str_to_category
from track_insights.database import DatabaseConnection
from track_insights.database.models import Athlete, Club, Discipline, Event, Result

bestlist_bp = Blueprint("bestlist", __name__)

MAX_AMOUNT_RESULTS = 5000


# pylint: disable=too-many-locals,too-many-branches
@bestlist_bp.route("/", methods=["GET"])
def get_bestlist() -> Response:
    year = request.args.get("year", type=int)
    category, _ = str_to_category(request.args.get("category_identifier", type=str))
    discipline_id = request.args.get("discipline_id", type=int)
    only_homologated = str_to_bool(request.args.get("only_homologated"), False)
    restrict_category = str_to_bool(request.args.get("restrict_category"), False)
    one_result_per_athlete = str_to_bool(request.args.get("one_result_per_athlete"), True)
    allow_wind = str_to_bool(request.args.get("allow_wind"), False)
    range_start = request.args.get("range_start", type=int)
    range_end = request.args.get("range_end", type=int)
    range_type = request.args.get("range_type", type=str)
    limit = min(request.args.get("limit", MAX_AMOUNT_RESULTS, type=int), MAX_AMOUNT_RESULTS)

    if discipline_id is None:
        return jsonify({"error": "No discipline identifier specified"}), 400

    filters = [Result.ignore.is_(False)]

    config = current_app.config["config"]
    with DatabaseConnection(config) as database:
        discipline: Optional[Discipline] = (
            database.session.query(Discipline).filter(Discipline.id == discipline_id).first()
        )

    if discipline is not None:
        filters.append(Result.discipline_id == discipline.id)
    else:
        return jsonify({"error": f"No discipline found with id {discipline_id}"}), 400

    if range_type is not None:
        if range_type not in {"performance", "score"}:
            return jsonify({"error": f"Invalid range type {range_type}"}), 400

        if range_type == "score" and discipline.score_identifier is not None:
            if range_start is not None:
                filters.append(Result.points >= range_start)
            if range_end is not None:
                filters.append(Result.points <= range_end)
        else:
            if range_start is not None:
                filters.append(Result.performance >= range_start)
            if range_end is not None:
                filters.append(Result.performance <= range_end)

    min_age, max_age = get_age_bounds(category, restrict_category)
    filters.append(
        and_(
            sqlalchemy.extract("year", Result.date) - sqlalchemy.extract("year", Athlete.birthdate) >= min_age,
            sqlalchemy.extract("year", Result.date) - sqlalchemy.extract("year", Athlete.birthdate) < max_age,
        )
    )

    if not allow_wind:
        filters.append(or_(Result.wind.is_(None), Result.wind <= 2.0))

    if year is not None:
        filters.append(sqlalchemy.extract("year", Result.date) == year)

    if only_homologated:
        filters.append(Result.homologated.is_(True))

    with DatabaseConnection(config) as database:
        base_table_cte = (
            database.session.query(
                Result.id,
                Result.athlete_id,
                Result.club_id,
                Result.event_id,
                Result.performance,
                Result.wind,
                Result.rank,
                Result.location,
                Result.date,
                Result.homologated,
                Result.points,
                Athlete.name.label("athlete_name"),
                Athlete.birthdate.label("birthdate"),
                Athlete.nationality.label("nationality"),
                Club.name.label("club_name"),
                Event.name.label("event_name"),
            )
            .join(Athlete, Result.athlete)
            .join(Club, Result.club)
            .join(Event, Result.event)
            .filter(*filters)
            .cte("base_table")
        )

        if one_result_per_athlete:
            subquery = database.session.query(
                base_table_cte.c.id,
                func.row_number()
                .over(
                    partition_by=base_table_cte.c.athlete_id,
                    order_by=[
                        (
                            base_table_cte.c.performance.asc()
                            if discipline.config.is_ascending()
                            else base_table_cte.c.performance.desc()
                        ),
                        base_table_cte.c.date.desc(),
                    ],
                )
                .label("rn"),
            ).subquery()

            results: list[Any] = (
                database.session.query(base_table_cte)
                .join(subquery, subquery.c.id == base_table_cte.c.id)
                .filter(subquery.c.rn == 1)
                .order_by(
                    (
                        base_table_cte.c.performance.asc()
                        if discipline.config.is_ascending()
                        else base_table_cte.c.performance.desc()
                    ),
                    base_table_cte.c.date.asc(),
                )
                .limit(limit)
                .all()
            )
        else:
            results: list[Any] = (  # type: ignore
                database.session.query(base_table_cte)
                .order_by(
                    (
                        base_table_cte.c.performance.asc()
                        if discipline.config.is_ascending()
                        else base_table_cte.c.performance.desc()
                    ),
                    base_table_cte.c.date.asc(),
                )
                .limit(limit)
                .all()
            )

    wind_relevant = any(result.wind is not None for result in results)
    homologation_relevant = any(not result.homologated for result in results)

    # Return a JSON response
    bestlist_dict = {
        "configuration": {
            "wind_relevant": wind_relevant,
            "homologation_relevant": homologation_relevant,
            "score_available": discipline.score_identifier is not None,
            "discipline_type": discipline.config.discipline_type.value,
        },
        "results": list(map(convert_result_to_json, results)),
    }
    return jsonify(bestlist_dict)


def convert_result_to_json(result: Any) -> dict:
    return {
        "athlete": {
            "id": result.athlete_id,
            "name": result.athlete_name,
            "birthdate": result.birthdate,
            "nationality": result.nationality,
        },
        "club": {
            "id": result.club_id,
            "name": result.club_name,
        },
        "event": {
            "id": result.event_id,
            "name": result.event_name,
        },
        "result": {
            "performance": result.performance,
            "wind": result.wind,
            "rank": result.rank,
            "location": result.location,
            "date": result.date,
            "homologated": result.homologated,
            "points": result.points,
        },
    }
