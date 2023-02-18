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
        self.authorized_request("post", "/folders/mkdir", json={"path": "/folder"})
        created_folder = self.session.query(models.FolderRecord).filter_by(
            owner=self.key_record,
            full_path="/folder"
        ).first()
        self.assertEqual(created_folder.name, "folder")

    def test_create_folder_recursive(self):
        self.authorized_request("post", "/folders/mkdir", json={
            "path": "/grandparent/parent/child",
            "recursive": True
        })
        nested_folder = self.session.query(models.FolderRecord).filter_by(
            owner=self.key_record,
            full_path="/grandparent/parent/child"
        ).first()
        self.assertEqual(nested_folder.parent_folder.name, "parent")
