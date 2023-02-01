from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from api import config
from api.app import app
from api.db import engine as db
from api.db.dependency import create_get_db_dependency
from api.dependencies import get_db

test_settings = config.Settings(_env_file=".config.test")


def setup_config() -> config.Settings:
    config.settings = test_settings
    return config.settings


def setup_database() -> Session:
    db.engine = create_engine(test_settings.database_url)
    db.Base.metadata.create_all(db.engine)
    app.dependency_overrides[get_db] = create_get_db_dependency(sessionmaker(db.engine))
    session = Session(db.engine)
    return session


def teardown_database(session: Session):
    session.close()
    db.Base.metadata.drop_all(db.engine)
