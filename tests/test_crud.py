from api.db import crud, models
from tests.base_tests import TestWithKeyRecord


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
        self.assertEqual(child_folder.owner_id, self.key_record.id)
        self.assertEqual(child_folder.full_path, "parent_folder/child_folder")

    def test_create_folders_recursively(self):
        nested_folder = crud.create_folders_recursively(
            self.session,
            self.key_record,
            "/great_grandparent/grandparent/parent/child"
        )
        root_folder = nested_folder.parent_folder.parent_folder.parent_folder.parent_folder
        self.assertEqual(root_folder.owner, self.key_record)

    def test_rename_folder(self):
        grandparent = models.FolderRecord(
            owner=self.key_record,
            name="grandparent",
            full_path="grandparent"
        )
        parent = models.FolderRecord(
            owner=self.key_record,
            parent_folder=grandparent,
            name="parent",
            full_path="grandparent/parent"
        )
        child = models.FolderRecord(
            owner=self.key_record,
            parent_folder=parent,
            name="child",
            full_path="grandparent/parent/child"
        )
        self.session.add_all((grandparent, parent, child))
        self.session.commit()
        self.session.refresh(grandparent)
        updated_grandparent = crud.rename_folder(self.session, grandparent, "renamed")
        child_full_path = updated_grandparent.child_folders[0].child_folders[0].full_path
        self.assertEqual(child_full_path, "renamed/parent/child")

    def test_move_folder(self):
        folder_record = models.FolderRecord(
            owner=self.key_record,
            name="folder",
            full_path="folder"
        )
        child_folder = models.FolderRecord(
            owner=self.key_record,
            parent_folder=folder_record,
            name="child",
            full_path="folder/child"
        )
        destination_folder = models.FolderRecord(
            owner=self.key_record,
            name="destination",
            full_path="destination"
        )
        self.session.add_all((folder_record, child_folder, destination_folder))
        self.session.commit()
        self.session.refresh(folder_record)
        self.session.refresh(destination_folder)
        updated_folder_record = crud.move_folder(self.session, folder_record, destination_folder)
        updated_child_folder = updated_folder_record.child_folders[0]
        self.assertEqual(updated_child_folder.full_path, "destination/folder/child")

    def test_list_folder(self):
        parent_folder = models.FolderRecord(
            owner=self.key_record,
            name="parent_folder",
            full_path="parent_folder"
        )
        child_names = [f"folder{i}" for i in range(3)]
        for child_folder_name in child_names:
            child_folder = models.FolderRecord(
                owner=self.key_record,
                name=child_folder_name,
                full_path=f"parent_folder/{child_folder_name}"
            )
            parent_folder.child_folders.append(child_folder)
        self.session.add(parent_folder)
        self.session.commit()
        self.session.refresh(parent_folder)
        folder_content = crud.list_folder(parent_folder)
        self.assertListEqual(folder_content.folders, child_names)
