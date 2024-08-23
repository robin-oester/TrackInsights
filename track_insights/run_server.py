import argparse
import logging

import yaml
from flask import Flask
from flask_cors import CORS
from track_insights.blueprints import bestlist_bp, disciplines_bp
from track_insights.common import CONFIG_PATH, CONFIG_SCHEMA_PATH, validate_json
from track_insights.database import DatabaseConnection

logging.basicConfig(
    level=logging.NOTSET,
    format="[%(asctime)s]  [%(filename)15s:%(lineno)4d] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
)
logger = logging.getLogger(__name__)

APP = Flask(__name__)
APP.register_blueprint(bestlist_bp, url_prefix="/api/bestlist")
APP.register_blueprint(disciplines_bp, url_prefix="/api/disciplines")
CORS(
    APP,
    resources={
        r"/api/*": {"origins": ["http://localhost:5173"], "methods": ["GET", "POST"], "allow_headers": ["Content-Type"]}
    },
)


def main() -> None:
    parser = argparse.ArgumentParser(description="TrackInsights - Flask Server")

    parser.add_argument(
        "-p", "--port", type=int, required=True, help="Specify the port on which to run the flask server."
    )
    parser.add_argument("--debug", action="store_true", help="Run in debug mode.")

    args = parser.parse_args()

    logger.info("Checking configuration file and initialize database...")
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config: dict = yaml.safe_load(config_file)
    if not check_configuration(config):
        return

    APP.config["config"] = config
    APP.run(port=args.port, debug=args.debug)


def check_configuration(config: dict) -> bool:
    valid_yaml, exception = validate_json(config, CONFIG_SCHEMA_PATH)

    if not valid_yaml:
        logger.error(f"Error while validating pipeline configuration file for schema-compliance: {exception.message}")
        logger.error(exception)
        return False

    with DatabaseConnection(config) as database:
        database.create_tables()
    return True


if __name__ == "__main__":
    main()
