from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from api.db import crud, models
from api.schemas.storage_api import StorageSpaceResponse, UploadRequestHeaders
from api.utils.storage import StorageClient
from tests.base_tests import TestWithRegisteredKey


def _stream_generator():
    yield bytes()


class TestStorageClient(IsolatedAsyncioTestCase, TestWithRegisteredKey):
    @patch("aiohttp.ClientSession.post")
    async def test_upload_existing_file(self, request_mock: AsyncMock):
        storage_response = StorageSpaceResponse(
            used=10,
            capacity=10000000
        )
        request_mock.return_value.__aenter__.return_value.ok = True
        request_mock.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=storage_response
        )
        storage_record = models.StorageRecord(
            id="storage_id",
            url="https://storage",
            token="token"
        )
        folder_record = models.FolderRecord(
            owner=self.key_record,
            name="folder",
            full_path="folder"
        )
        existing_file_record = models.FileRecord(
            folder=folder_record,
            storage=storage_record,
            filename="filename",
            full_path="folder/filename",
            size=0
        )
        crud.update_record(self.session, existing_file_record)
        prev_modified = existing_file_record.last_modified

        storage_client = StorageClient(self.session, self.key_record, storage_record)
        new_file_size = 200
        file_record = await storage_client.upload_file(
            "folder/filename",
            new_file_size,
            _stream_generator
        )
        crud.update_record(self.session, storage_record)
        crud.update_record(self.session, file_record)

        self.assertEqual(storage_record.used_space, storage_response.used)
        self.assertEqual(file_record.size, new_file_size)
        self.assertGreater(file_record.last_modified, prev_modified)
        request_mock.assert_called_once_with(
            f"{storage_record.url}/{file_record.id}",
            data=_stream_generator,
            headers=UploadRequestHeaders(
                authorization=storage_record.token,
                file_size=new_file_size
            ).dict(by_alias=True)
        )

    @patch("aiohttp.ClientSession.post")
    async def test_upload_new_file(self, request_mock: AsyncMock):
        storage_response = StorageSpaceResponse(
            used=10,
            capacity=10000000
        )
        request_mock.return_value.__aenter__.return_value.ok = True
        request_mock.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=storage_response
        )
        storage_record = models.StorageRecord(
            id="storage_id",
            url="https://storage",
            token="token"
        )
        folder_record = models.FolderRecord(
            owner=self.key_record,
            name="folder",
            full_path="folder"
        )
        crud.update_record(self.session, folder_record)

        storage_client = StorageClient(self.session, self.key_record, storage_record)
        file_size = 200
        file_record = await storage_client.upload_file(
            "folder/filename",
            file_size,
            _stream_generator
        )
        crud.update_record(self.session, storage_record)
        crud.update_record(self.session, file_record)

        self.assertEqual(storage_record.used_space, storage_response.used)
        self.assertEqual(file_record.storage_id, storage_record.id)
        self.assertEqual(file_record.folder.id, folder_record.id)
        request_mock.assert_called_once_with(
            f"{storage_record.url}/{file_record.id}",
            data=_stream_generator,
            headers=UploadRequestHeaders(
                authorization=storage_record.token,
                file_size=file_size
            ).dict(by_alias=True)
        )
