from operator import and_

import sqlalchemy
from flask import Blueprint, Response, current_app, jsonify, request
from sqlalchemy import Row
from sqlalchemy.sql.functions import count
from track_insights.blueprints.utils import get_age_bounds, str_to_bool, str_to_category
from track_insights.database import DatabaseConnection
from track_insights.database.models import Athlete, Discipline, DisciplineConfiguration, Result

disciplines_bp = Blueprint("disciplines", __name__)


@disciplines_bp.route("/", methods=["GET"])
def get_available_disciplines() -> Response:
    year = request.args.get("year", type=int)
    category, male = str_to_category(request.args.get("category_identifier", type=str))
    only_homologated = str_to_bool(request.args.get("only_homologated"), False)
    indoor = str_to_bool(request.args.get("indoor"), False)
    restrict_category = str_to_bool(request.args.get("restrict_category"), False)
    score_available = str_to_bool(request.args.get("score_available"), False)

    filters = [Result.ignore.is_(False), Discipline.male.is_(male), Discipline.indoor.is_(indoor)]

    min_age, max_age = get_age_bounds(category, restrict_category)
    filters.append(
        and_(
            sqlalchemy.extract("year", Result.date) - sqlalchemy.extract("year", Athlete.birthdate) >= min_age,
            sqlalchemy.extract("year", Result.date) - sqlalchemy.extract("year", Athlete.birthdate) < max_age,
        )
    )

    if score_available:
        filters.append(Discipline.score_identifier.isnot(None))

    if year is not None:
        filters.append(sqlalchemy.extract("year", Result.date) == year)

    if only_homologated:
        filters.append(Result.homologated.is_(True))

    config = current_app.config["config"]
    with DatabaseConnection(config) as database:
        disciplines: list[Row] = (
            database.session.query(
                Result.discipline_id,
                DisciplineConfiguration.name,
                Discipline.score_identifier,
                count(Result.wind).label("wind_results"),
            )
            .join(Athlete, Result.athlete)
            .join(Discipline, Result.discipline)
            .join(DisciplineConfiguration, Discipline.config)
            .filter(*filters)
            .group_by(Result.discipline_id, DisciplineConfiguration.name, Discipline.score_identifier)
            .all()
        )

    return jsonify(
        {
            "disciplines": [
                {
                    "id": row.discipline_id,
                    "name": row.name,
                    "score_available": row.score_identifier is not None,
                    "wind_relevant": row.wind_results > 0,
                }
                for row in disciplines
            ]
        }
    )
