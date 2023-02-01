from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from api import config
from api.app import app
from api.db import engine as db
from api.dependencies import get_db
from api.utils.db import create_get_db_dependency

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
