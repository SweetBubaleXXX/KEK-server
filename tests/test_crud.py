from sqlalchemy import func, select

from api.db import crud, models
from tests.base_tests import TestWithDatabase
from tests.setup_test_env import KEY, KEY_ID


class TestCrud(TestWithDatabase):
    async def test_get_key(self):
        found_key = await crud.get_key_by_id(self.session, KEY_ID)
        self.assertEqual(found_key.public_key, KEY.public_key.serialize().decode())

    async def test_get_key_not_found(self):
        found_key = await crud.get_key_by_id(self.session, "unknown_id")
        self.assertIsNone(found_key)

    async def test_add_key(self):
        key_id = "key_id"
        await crud.add_key(self.session, key_id, "public_key")
        await self.session.commit()
        key_record = (
            await self.session.scalars(
                select(models.KeyRecord).filter(models.KeyRecord.id == key_id)
            )
        ).first()
        self.assertEqual(
            key_record.storage_size_limit, self.settings.user_storage_size_limit
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
                select(models.FolderRecord).filter(
                    models.FolderRecord.owner_id == key_id,
                    models.FolderRecord.full_path == models.ROOT_PATH,
                )
            )
        ).first()
        self.assertEqual((await folder_record.awaitable_attrs.owner).id, key_id)

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
                .filter(
                    models.FolderRecord.owner_id == key_id,
                    models.FolderRecord.full_path == models.ROOT_PATH,
                )
            )
        ) or 0
        self.assertEqual(root_folder_count, 1)

    async def test_create_child_folder(self):
        parent_folder = models.FolderRecord(
            owner=self.key_record, name="parent_folder", full_path="parent_folder"
        )
        self.session.add(parent_folder)
        await self.session.commit()
        await self.session.refresh(parent_folder)
        child_folder = await crud.create_child_folder(
            self.session, parent_folder, "child_folder"
        )
        self.assertEqual(child_folder.owner_id, KEY_ID)
        self.assertEqual(child_folder.full_path, "parent_folder/child_folder")

    async def test_create_folders_recursively(self):
        nested_folder = await crud.create_folders_recursively(
            self.session, self.key_record, "/great_grandparent/grandparent/parent/child"
        )
        root_folder = await (
            await (
                await (
                    await nested_folder.awaitable_attrs.parent_folder
                ).awaitable_attrs.parent_folder
            ).awaitable_attrs.parent_folder
        ).awaitable_attrs.parent_folder
        self.assertEqual(await root_folder.awaitable_attrs.owner, self.key_record)

    async def test_rename_folder(self):
        grandparent = models.FolderRecord(
            owner=self.key_record, name="grandparent", full_path="grandparent"
        )
        parent = models.FolderRecord(
            owner=self.key_record,
            parent_folder=grandparent,
            name="parent",
            full_path="grandparent/parent",
        )
        child = models.FolderRecord(
            owner=self.key_record,
            parent_folder=parent,
            name="child",
            full_path="grandparent/parent/child",
        )
        self.session.add_all((grandparent, parent, child))
        await self.session.commit()
        await self.session.refresh(grandparent)
        updated_grandparent = await crud.rename_folder(
            self.session, grandparent, "renamed"
        )
        child_full_path = (
            await (await updated_grandparent.awaitable_attrs.child_folders)[
                0
            ].awaitable_attrs.child_folders
        )[0].full_path
        self.assertEqual(child_full_path, "renamed/parent/child")

    async def test_move_folder(self):
        folder_record = models.FolderRecord(
            owner=self.key_record, name="folder", full_path="folder"
        )
        child_folder = models.FolderRecord(
            owner=self.key_record,
            parent_folder=folder_record,
            name="child",
            full_path="folder/child",
        )
        destination_folder = models.FolderRecord(
            owner=self.key_record, name="destination", full_path="destination"
        )
        self.session.add_all((folder_record, child_folder, destination_folder))
        await self.session.commit()
        await self.session.refresh(folder_record)
        await self.session.refresh(destination_folder)
        updated_folder_record = await crud.move_folder(
            self.session, folder_record, destination_folder
        )
        updated_child_folder = (
            await updated_folder_record.awaitable_attrs.child_folders
        )[0]
        self.assertEqual(updated_child_folder.full_path, "destination/folder/child")

    async def test_list_folder(self):
        parent_folder = models.FolderRecord(
            owner=self.key_record, name="parent_folder", full_path="parent_folder"
        )
        child_names = [f"folder{i}" for i in range(3)]
        for child_folder_name in child_names:
            child_folder = models.FolderRecord(
                owner=self.key_record,
                name=child_folder_name,
                full_path=f"parent_folder/{child_folder_name}",
            )
            parent_folder.child_folders.append(child_folder)
        self.session.add(parent_folder)
        await self.session.commit()
        await self.session.refresh(parent_folder)
        folder_content = await parent_folder.json()
        self.assertListEqual(folder_content.folders, child_names)

    async def test_folder_size(self):
        parent_folder = models.FolderRecord(
            owner=self.key_record, name="parent_folder", full_path="parent_folder"
        )
        expected_size = 0
        child_names = [f"folder{i}" for i in range(3)]
        for child_folder_name in child_names:
            child_folder = models.FolderRecord(
                owner=self.key_record,
                name=child_folder_name,
                full_path=f"parent_folder/{child_folder_name}",
            )
            for i in range(10):
                filename = f"file_{i}"
                child_folder.files.append(
                    models.FileRecord(
                        filename=filename,
                        full_path=f"{child_folder.full_path}/{filename}",
                        size=i,
                    )
                )
                expected_size += i
            parent_folder.child_folders.append(child_folder)
        self.session.add(parent_folder)
        await self.session.commit()
        await self.session.refresh(parent_folder)
        self.assertEqual(parent_folder.size, expected_size)

    async def test_create_file_record(self):
        folder_record = models.FolderRecord(
            owner=self.key_record, name="folder", full_path="folder"
        )
        storage_record = models.StorageRecord(id="id", url="url", token="token")
        file_record = await crud.create_file_record(
            self.session, folder_record, "filename", storage_record, 0
        )
        self.assertEqual(file_record.full_path, "folder/filename")

    async def test_calculate_used_storage(self):
        folder_record = models.FolderRecord(owner=self.key_record)
        size_range = range(1, 10)
        for size in size_range:
            self.session.add(
                models.FileRecord(
                    folder=folder_record,
                    filename=str(size),
                    full_path=f"/{size}",
                    size=size,
                )
            )
        await self.session.commit()
        await self.session.refresh(folder_record)
        calculated_size = await crud.calculate_used_storage(
            self.session, self.key_record
        )
        expected_size = sum(size_range)
        self.assertEqual(calculated_size, expected_size)
