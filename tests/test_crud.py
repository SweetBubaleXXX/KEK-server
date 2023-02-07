from api.db import crud, models
from tests.setup_test_env import TestWithKeyRecord


class TestCrud(TestWithKeyRecord):
    def test_get_key(self):
        found_key = crud.get_key_by_id(self.session, self.key_record.id)
        self.assertEqual(found_key.public_key, self.key_record.public_key)

    def test_get_key_not_found(self):
        found_key = crud.get_key_by_id(self.session, "unknown_id")
        self.assertIsNone(found_key)

    def test_add_key(self):
        key_id = "key_id"
        crud.add_key(self.session, key_id, "public_key")
        key_record = self.session.query(models.KeyRecord).filter_by(id=key_id).first()
        self.assertEqual(key_record.storage_size_limit, self.settings.user_storage_size_limit)

    def test_find_folder(self):
        folder_record = models.FolderRecord(
            owner=self.key_record,
            name="folder",
            full_path="folder"
        )
        self.session.add(folder_record)
        self.session.commit()
        self.session.refresh(folder_record)
        found_folder = crud.find_folder(
            self.session,
            owner_id=self.key_record.id,
            name="folder"
        )
        self.assertEqual(found_folder.owner, self.key_record)

    def test_create_root_folder(self):
        crud.return_or_create_root_folder(self.session, self.key_record)
        folder_record = self.session.query(models.FolderRecord).filter_by(
            owner_id=self.key_record.id,
            full_path=models.ROOT_PATH
        ).first()
        self.assertEqual(folder_record.owner, self.key_record)

    def test_create_root_folder_twice(self):
        crud.return_or_create_root_folder(self.session, self.key_record)
        crud.return_or_create_root_folder(self.session, self.key_record)
        root_folder_count = self.session.query(models.FolderRecord).filter_by(
            owner_id=self.key_record.id,
            full_path=models.ROOT_PATH
        ).count()
        self.assertEqual(root_folder_count, 1)

    def test_create_child_folder(self):
        parent_folder = models.FolderRecord(
            owner=self.key_record,
            name="parent_folder",
            full_path="parent_folder"
        )
        self.session.add(parent_folder)
        self.session.commit()
        self.session.refresh(parent_folder)
        child_folder = crud.create_child_folder(self.session, parent_folder, "child_folder")
        self.assertEqual(child_folder.full_path, "parent_folder/child_folder")

    def test_create_folders_recursively(self):
        nested_folder = crud.create_folders_recursively(
            self.session,
            self.key_record,
            "/great_grandfather/grandfather/parent/child"
        )
        root_folder = nested_folder.parent_folder.parent_folder.parent_folder.parent_folder
        self.assertEqual(root_folder.owner, self.key_record)
