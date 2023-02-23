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

    def test_move_folder(self):  # Not working
        response = self.authorized_request("post", "/folders/mkdir", json={
            "path": "/parent_1/child",
            "recursive": True
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.authorized_request("post", "/folders/mkdir", json={"path": "/parent_1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.authorized_request("post", "/folders/move", json={})

    def test_delete_folder(self):  # Not working
        response = self.authorized_request("post", "/folders/mkdir", json={"path": "/folder"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.authorized_request("delete", "/folders/rmdir", headers={"path": "/folder"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        folder_still_exists = self.session.query(models.FolderRecord).filter_by(
            owner=self.key_record,
            full_path="/folder"
        ).count()
        self.assertFalse(folder_still_exists)
