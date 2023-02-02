import unittest

from api.db import crud, models
from tests.setup_test_env import (setup_config, setup_database,
                                  teardown_database)


class TestCrud(unittest.TestCase):
    def setUp(self):
        self.settings = setup_config()
        self.session = setup_database()

    def tearDown(self):
        teardown_database(self.session)

    def test_get_key(self):
        key_id = "key_id"
        public_key = "public_key"
        key_record = models.KeyRecord(id=key_id, public_key=public_key)
        self.session.add(key_record)
        self.session.commit()
        found_key = crud.get_key_by_id(self.session, key_id)
        self.assertEqual(found_key.public_key, public_key)

    def test_get_key_not_found(self):
        key_record = models.KeyRecord(id="key_id", public_key="public_key")
        self.session.add(key_record)
        self.session.commit()
        found_key = crud.get_key_by_id(self.session, "unknown_id")
        self.assertIsNone(found_key)

    def test_add_key(self):
        key_id = "key_id"
        crud.add_key(self.session, key_id, "public_key")
        key_record = self.session.query(models.KeyRecord).filter_by(id=key_id).first()
        self.assertEqual(key_record.storage_size_limit, self.settings.user_storage_size_limit)

    def test_create_root_folder(self):
        key_record = models.KeyRecord(id="key_id", public_key="public_key")
        self.session.add(key_record)
        self.session.commit()
        crud.return_or_create_root_folder(self.session, key_record)
        folder_record = self.session.query(models.FolderRecord).filter_by(
            owner_id=key_record.id,
            full_path=models.ROOT_PATH
        ).first()
        self.assertEqual(folder_record.owner, key_record)

    def test_create_root_folder_twice(self):
        key_record = models.KeyRecord(id="key_id", public_key="public_key")
        self.session.add(key_record)
        self.session.commit()
        crud.return_or_create_root_folder(self.session, key_record)
        crud.return_or_create_root_folder(self.session, key_record)
        root_folder_count = self.session.query(models.FolderRecord).filter_by(
            owner_id=key_record.id,
            full_path=models.ROOT_PATH
        ).count()
        self.assertEqual(root_folder_count, 1)
