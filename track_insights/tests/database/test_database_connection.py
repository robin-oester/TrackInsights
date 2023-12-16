from track_insights.database import DatabaseConnection


def get_minimal_config() -> dict:
    return {
        "database": {
            "drivername": "sqlite",
            "username": "",
            "password": "",
            "host": "",
            "port": 0,
            "database": ":memory:",
        }
    }


def test_database_connection():
    config = get_minimal_config()
    with DatabaseConnection(get_minimal_config()) as database:
        database.create_tables()
        assert database.session is not None
        assert database.config == config

        assert database.drivername == "sqlite"
        assert database.username == ""
        assert database.password == ""
        assert database.host == ""
        assert database.port == 0
        assert database.database == ":memory:"
