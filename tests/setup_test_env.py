import unittest

from KEK.hybrid import PrivateKEK
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from api import config
from api.app import app
from api.db import engine as db
from api.db import models
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


class TestWithDatabase(unittest.TestCase):
    def setUp(self):
        self.settings = setup_config()
        self.session = setup_database()

    def tearDown(self):
        teardown_database(self.session)


class TestWithKeyRecord(TestWithDatabase):
    def setUp(self):
        super().setUp()
        self.key = PrivateKEK.generate()
        self.key_record = self._add_key_to_db()

    def _add_key_to_db(self) -> models.KeyRecord:
        key_record = models.KeyRecord(
            id=self.key.key_id.hex(),
            public_key=self.key.public_key.serialize().decode("utf-8")
        )
        self.session.add(key_record)
        self.session.commit()
        self.session.refresh(key_record)
        return key_record
