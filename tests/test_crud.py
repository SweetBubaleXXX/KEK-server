import unittest

from api.db import crud, engine, models
from tests.setup_test_env import (setup_config, setup_database,
                                  teardown_database)


class TestCrud(unittest.TestCase):
    def setUp(self):
        self.settings = setup_config()
        self.engine, self.session = setup_database(engine.Base)

    def test_get_key(self):
        key_id = "key_id"
        public_key = "public_key"
        key_record = models.KeyRecord(id=key_id, public_key=public_key)
        self.session.add(key_record)
        self.session.commit()
        found_key = crud.get_key(self.session, key_id)
        self.assertEqual(found_key.public_key, public_key)

    def test_get_key_not_found(self):
        key_record = models.KeyRecord(id="key_id", public_key="public_key")
        self.session.add(key_record)
        self.session.commit()
        found_key = crud.get_key(self.session, "unknown_id")
        self.assertIsNone(found_key)

    def test_add_key(self):
        key_id = "key_id"
        crud.add_key(self.session, key_id, "public_key")
        key_record = self.session.query(models.KeyRecord).filter_by(id=key_id).first()
        self.assertEqual(key_record.storage_size_limit, self.settings.user_storage_size_limit)

    def tearDown(self):
        teardown_database(engine.Base, self.engine)
