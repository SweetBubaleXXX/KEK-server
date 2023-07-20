from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from api.db import models
from tests.base_tests import TestWithClient, add_test_authentication
from tests.setup_test_env import KEY_ID


@add_test_authentication(
    ("get", "/folders/list"),
    ("post", "/folders/mkdir"),
    ("delete", "/folders/rmdir"),
)
class TestFolders(TestWithClient):
    def test_create_folder_parent_not_exists(self):
        response = self.authorized_request(
            "post", "/folders/mkdir", json={"path": "/nonexistent_parent/child"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    async def test_create_folder(self):
        response = self.authorized_request(
            "post", "/folders/mkdir", json={"path": "/folder"}
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        created_folder = (
            await self.session.scalars(
                select(models.FolderRecord).where(
                    models.FolderRecord.owner_id == KEY_ID,
                    models.FolderRecord.full_path == "/folder",
                )
            )
        ).one()
        self.assertEqual(created_folder.name, "folder")

    def test_create_folder_already_exists(self):
        response = self.authorized_request(
            "post", "/folders/mkdir", json={"path": "/a1"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    async def test_create_folder_recursive(self):
        response = self.authorized_request(
            "post",
            "/folders/mkdir",
            json={"path": "/grandparent/parent/child", "recursive": True},
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        nested_folder = (
            await self.session.scalars(
                select(models.FolderRecord)
                .options(joinedload(models.FolderRecord.parent_folder))
                .filter(
                    models.FolderRecord.owner_id == KEY_ID,
                    models.FolderRecord.full_path == "/grandparent/parent/child",
                )
            )
        ).one()
        self.assertEqual(nested_folder.parent_folder.name, "parent")

    async def test_rename_folder(self):
        response = self.authorized_request(
            "post",
            "/folders/rename",
            json={"path": "/a1", "new_name": "renamed"},
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        renamed_child = (
            await self.session.scalars(
                select(models.FolderRecord)
                .options(joinedload(models.FolderRecord.parent_folder))
                .filter(
                    models.FolderRecord.owner_id == KEY_ID,
                    models.FolderRecord.full_path == "/renamed/b1",
                )
            )
        ).one()
        self.assertEqual(
            renamed_child.parent_folder.name,
            "renamed",
        )

    def test_rename_folder_already_exists(self):
        response = self.authorized_request(
            "post",
            "/folders/rename",
            json={"path": "/a1", "new_name": "a2"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rename_folder_not_exists(self):
        response = self.authorized_request(
            "post",
            "/folders/rename",
            json={"path": "/nonexistent_folder", "new_name": "renamed"},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_folder(self):
        response = self.authorized_request(
            "get", "/folders/list", headers={"path": "/a1"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        child_names = response.json()["folders"]
        files = response.json()["files"]
        self.assertListEqual(child_names, ["b1", "b2"])
        self.assertEqual(len(files), 4)

    def test_list_folder_not_exists(self):
        response = self.authorized_request(
            "get", "/folders/list", headers={"path": "/nonexistent_path"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    async def test_move_folder(self):
        response = self.authorized_request(
            "post",
            "/folders/move",
            json={"path": "/a1/b1", "destination": "/a1/b2"},
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        old_parent = (
            await self.session.scalars(
                select(models.FolderRecord)
                .options(selectinload(models.FolderRecord.child_folders))
                .filter(
                    models.FolderRecord.owner_id == KEY_ID,
                    models.FolderRecord.full_path == "/a1",
                )
            )
        ).one()
        self.assertEqual(len(old_parent.child_folders), 1)

    def test_move_folder_invalid_destination(self):
        response = self.authorized_request(
            "post",
            "/folders/move",
            json={"path": "/a1", "destination": "/a1/b1"},
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_move_folder_not_exists(self):
        response = self.authorized_request(
            "post",
            "/folders/move",
            json={
                "path": "/nonexistent_path",
                "destination": "/nonexistent_destination",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    async def test_delete_folder(self):
        response = self.authorized_request(
            "delete", "/folders/rmdir", headers={"path": "/a1/b1/c1"}
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        deleted_folder = (
            await self.session.scalars(
                select(models.FolderRecord).where(
                    models.FolderRecord.owner_id == KEY_ID,
                    models.FolderRecord.full_path == "/a1/b1/c1",
                )
            )
        ).first()
        self.assertIsNone(deleted_folder)

    def test_delete_folder_not_exists(self):
        response = self.authorized_request(
            "delete", "/folders/rmdir", headers={"path": "/nonexistent_path"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
