from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from api import config
from api.db import engine as db

test_settings = config.Settings(_env_file=".config.test")


def setup_config() -> config.Settings:
    config.settings = test_settings
    return config.settings


def setup_database(Base) -> tuple[Engine, Session]:
    db.engine = create_engine(test_settings.database_url)
    db.SessionLocal = sessionmaker(db.engine)
    session = Session(db.engine)
    Base.metadata.create_all(db.engine)
    return db.engine, session


def teardown_database(Base, engine: Engine):
    Base.metadata.drop_all(engine)
