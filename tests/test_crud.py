from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload

from api.db import crud, models
from tests.base_tests import TestWithDatabase
from tests.setup_test_env import FILE_SIZE, KEY, KEY_ID


class TestCrud(TestWithDatabase):
    async def test_get_key(self):
        found_key = await self.session.get(models.KeyRecord, KEY_ID)
        self.assertEqual(found_key.public_key, KEY.public_key.serialize().decode())

    async def test_get_key_not_found(self):
        found_key = await self.session.get(models.KeyRecord, "unknown_id")
        self.assertIsNone(found_key)

    async def test_add_key(self):
        key_id = "key_id"
        await crud.add_key(self.session, key_id, "public_key")
        await self.session.commit()
        key_record = (
            await self.session.scalars(
                select(models.KeyRecord).where(models.KeyRecord.id == key_id)
            )
        ).one()
        self.assertEqual(
            key_record.storage_size_limit, self.settings.USER_STORAGE_SIZE_LIMIT
        )

    async def test_find_file(self):
        found_file = await crud.find_file(
            self.session, await self.key_record, full_path="/a1/f1"
        )
        self.assertIsNotNone(found_file)
        self.assertEqual(found_file.filename, "f1")

    async def test_file_not_found(self):
        file_record = await crud.find_file(
            self.session, await self.key_record, full_path="non_existent_path"
        )
        self.assertIsNone(file_record)

    async def test_find_folder(self):
        found_folder = await crud.find_folder(
            self.session, owner=await self.key_record, full_path="/a2/b2"
        )
        self.assertEqual(found_folder.owner_id, KEY_ID)

    async def test_create_root_folder(self):
        key_id = "key_id"
        key_record = await crud.add_key(self.session, key_id, "public_key")
        await crud.return_or_create_root_folder(self.session, key_record)
        await self.session.commit()
        folder_record = (
            await self.session.scalars(
                select(models.FolderRecord)
                .options(joinedload(models.FolderRecord.owner))
                .where(
                    models.FolderRecord.owner_id == key_id,
                    models.FolderRecord.full_path == models.ROOT_PATH,
                )
            )
        ).one()
        self.assertEqual(folder_record.owner.id, key_id)

    async def test_create_root_folder_twice(self):
        key_id = "key_id"
        key_record = await crud.add_key(self.session, key_id, "public_key")
        await crud.return_or_create_root_folder(self.session, key_record)
        await crud.return_or_create_root_folder(self.session, key_record)
        await self.session.commit()
        root_folder_count = (
            await self.session.scalar(
                select(func.count())
                .select_from(models.FolderRecord)
                .where(
                    models.FolderRecord.owner_id == key_id,
                    models.FolderRecord.full_path == models.ROOT_PATH,
                )
            )
        ) or 0
        self.assertEqual(root_folder_count, 1)

    async def test_create_child_folder(self):
        parent_folder = (
            await self.session.scalars(
                select(models.FolderRecord).where(
                    models.FolderRecord.owner_id == KEY_ID,
                    models.FolderRecord.full_path == "/a1",
                )
            )
        ).one()
        child_folder = await crud.create_child_folder(
            self.session, parent_folder, "child_folder"
        )
        self.assertEqual(child_folder.owner_id, KEY_ID)
        self.assertEqual(child_folder.full_path, "/a1/child_folder")

    async def test_create_folders_recursively(self):
        nested_folder = await crud.create_folders_recursively(
            self.session, await self.key_record, "/a2/b2/c/d"
        )
        self.assertEqual((await nested_folder.awaitable_attrs.parent_folder).name, "c")
        self.assertEqual(nested_folder.owner_id, KEY_ID)

    async def test_rename_folder(self):
        parent_folder = (
            await self.session.scalars(
                select(models.FolderRecord).where(
                    models.FolderRecord.owner_id == KEY_ID,
                    models.FolderRecord.full_path == "/a1",
                )
            )
        ).one()
        updated_parent = await crud.rename_folder(
            self.session, parent_folder, "renamed"
        )
        await self.session.commit()
        for child_folder in await updated_parent.awaitable_attrs.child_folders:
            self.assertTrue(child_folder.full_path.startswith("/renamed"))

    async def test_move_folder(self):
        folder_record = (
            await self.session.scalars(
                select(models.FolderRecord).where(
                    models.FolderRecord.owner_id == KEY_ID,
                    models.FolderRecord.full_path == "/a1",
                )
            )
        ).one()
        destination_folder = (
            await self.session.scalars(
                select(models.FolderRecord).where(
                    models.FolderRecord.owner_id == KEY_ID,
                    models.FolderRecord.full_path == "/a2",
                )
            )
        ).one()
        await crud.move_folder(self.session, folder_record, destination_folder)
        await self.session.commit()
        updated_child_folder = (
            await self.session.scalars(
                select(models.FolderRecord).where(
                    models.FolderRecord.owner_id == KEY_ID,
                    models.FolderRecord.full_path == "/a2/a1/b1",
                )
            )
        ).first()
        self.assertIsNotNone(updated_child_folder)

    async def test_list_folder(self):
        folder_record = (
            await self.session.scalars(
                select(models.FolderRecord).where(
                    models.FolderRecord.owner_id == KEY_ID,
                    models.FolderRecord.full_path == "/a1",
                )
            )
        ).one()
        folder_content = await folder_record.json()
        self.assertListEqual(folder_content.folders, ["b1", "b2"])
        self.assertListEqual(
            [file.name for file in folder_content.files], ["f1", "f2", "f3", "f4"]
        )

    async def test_folder_size(self):
        folder_record = (
            await self.session.scalars(
                select(models.FolderRecord)
                .options(
                    selectinload(models.FolderRecord.child_folders),
                    selectinload(models.FolderRecord.files),
                )
                .where(
                    models.FolderRecord.owner_id == KEY_ID,
                    models.FolderRecord.full_path == "/a1",
                )
            )
        ).one()
        expected_size = (
            len(folder_record.files) * FILE_SIZE
            + len(folder_record.child_folders) * FILE_SIZE * 3
        )
        self.assertEqual(await folder_record.size, expected_size)

    async def test_create_file_record(self):
        folder_record = (
            await self.session.scalars(
                select(models.FolderRecord).where(
                    models.FolderRecord.owner_id == KEY_ID,
                    models.FolderRecord.full_path == "/a1/b1",
                )
            )
        ).one()
        storage_record = (
            await self.session.scalars(select(models.StorageRecord))
        ).one()
        file_record = await crud.create_file_record(
            self.session, folder_record, "filename", storage_record, 5
        )
        await self.session.commit()
        await self.session.refresh(file_record)
        self.assertEqual(file_record.full_path, "/a1/b1/filename")

    async def test_calculate_used_storage(self):
        calculated_size = await crud.calculate_used_storage(
            self.session, await self.key_record
        )
        expected_size = 3 * (4 + 3 * 2) * FILE_SIZE
        self.assertEqual(calculated_size, expected_size)
