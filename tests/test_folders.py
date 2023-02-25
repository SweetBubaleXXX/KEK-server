from fastapi import status

from api.db import models
from tests.base_tests import TestWithRegisteredKey, add_test_authentication


@add_test_authentication("/folders/mkdir")
class TestFoldres(TestWithRegisteredKey):
    def test_create_folder_parent_not_exists(self):
        response = self.authorized_request("post", "/folders/mkdir", json={
            "path": "nonexistent_parent/child"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_folder(self):
        response = self.authorized_request("post", "/folders/mkdir", json={"path": "/folder"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        created_folder = self.session.query(models.FolderRecord).filter_by(
            owner=self.key_record,
            full_path="/folder"
        ).first()
        self.assertEqual(created_folder.name, "folder")

    def test_create_folder_recursive(self):
        response = self.authorized_request("post", "/folders/mkdir", json={
            "path": "/grandparent/parent/child",
            "recursive": True
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        nested_folder = self.session.query(models.FolderRecord).filter_by(
            owner=self.key_record,
            full_path="/grandparent/parent/child"
        ).first()
        self.assertEqual(nested_folder.parent_folder.name, "parent")

    def test_rename_folder(self):
        response = self.authorized_request("post", "/folders/mkdir", json={
            "path": "/grandparent/parent/child",
            "recursive": True
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.authorized_request("post", "/folders/rename", json={
            "path": "/grandparent",
            "new_name": "renamed_grandparent"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        renamed_child = self.session.query(models.FolderRecord).filter_by(
            owner=self.key_record,
            full_path="/renamed_grandparent/parent/child"
        ).first()
        self.assertEqual(renamed_child.parent_folder.parent_folder.name, "renamed_grandparent")

    def test_rename_folder_already_exists(self):
        response = self.authorized_request("post", "/folders/mkdir", json={
            "path": "/parent/child",
            "recursive": True
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.authorized_request("post", "/folders/mkdir", json={
            "path": "/parent/existing_child"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.authorized_request("post", "/folders/rename", json={
            "path": "/parent/child",
            "new_name": "existing_child"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rename_folder_not_exists(self):
        response = self.authorized_request("post", "/folders/rename", json={
            "path": "/nonexistent_folder",
            "new_name": "renamed_grandparent"
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_folder(self):
        child_count = 5
        for i in range(child_count):
            response = self.authorized_request("post", "/folders/mkdir", json={
                "path": f"/parent/child_{i}",
                "recursive": True
            })
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.authorized_request("get", "/folders/list", headers={
            "path": "/parent"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        child_names = response.json()["folders"]
        self.assertEqual(len(child_names), child_count)

    def test_list_folder_not_exists(self):
        response = self.authorized_request("get", "/folders/list", headers={
            "path": "nonexistent_path"
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_move_folder(self):
        response = self.authorized_request("post", "/folders/mkdir", json={
            "path": "/parent/child",
            "recursive": True
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.authorized_request("post", "/folders/mkdir", json={"path": "/destination"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.authorized_request("post", "/folders/move", json={
            "path": "/parent/child",
            "destination": "/destination"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        old_parent = self.session.query(models.FolderRecord).filter_by(
            owner=self.key_record,
            full_path="/parent"
        ).first()
        old_parent_has_childs = bool(old_parent.child_folders)
        self.assertFalse(old_parent_has_childs)

    def test_move_folder_invalid_destination(self):
        response = self.authorized_request("post", "/folders/move", json={
            "path": "/parent",
            "destination": "/parent/child"
        })
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_move_folder_not_exists(self):
        response = self.authorized_request("post", "/folders/move", json={
            "path": "nonexistent_path",
            "destination": "nonexistent_destinations"
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
