import os


def build_database_url():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return database_url

    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_host = os.environ.get("DB_HOST")
    db_name = os.environ.get("DB_NAME")
    db_port = os.environ.get("DB_PORT")
    db_driver = os.environ.get("DB_DRIVER", "postgresql")

    if db_user and db_password and db_host and db_name:
        host = f"{db_host}:{db_port}" if db_port else db_host
        return f"{db_driver}://{db_user}:{db_password}@{host}/{db_name}"

    return None


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = build_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    IS_PRODUCTION = os.environ.get("FLASK_ENV") == "production"