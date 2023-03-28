from aiohttp import ClientSession

from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from api.db import models
from api.schemas.storage_api import StorageSpaceResponse, UploadRequestHeaders
from api.utils.storage import StorageClient
from tests.base_tests import TestWithRegisteredKey


class TestStorageClient(IsolatedAsyncioTestCase, TestWithRegisteredKey):
    @patch("aiohttp.ClientSession.post")
    async def test_upload_new_file(self, request_mock: AsyncMock):
        def stream_generator():
            yield bytes()

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
        self.session.add(existing_file_record)
        self.session.commit()
        self.session.refresh(existing_file_record)
        prev_modified = existing_file_record.last_modified

        storage_client = StorageClient(self.session, self.key_record, storage_record)
        new_file_size = 200
        file_record = await storage_client.upload_file(
            "folder/filename",
            new_file_size,
            stream_generator
        )
        self.session.add_all((storage_record, file_record))
        self.session.commit()
        self.session.refresh(storage_record)
        self.session.refresh(file_record)

        self.assertEqual(storage_record.used_space, storage_response.used)
        self.assertEqual(file_record.size, new_file_size)
        self.assertGreater(file_record.last_modified, prev_modified)
        request_mock.assert_called_once_with(
            f"{storage_record.url}/{file_record.id}",
            data=stream_generator,
            headers=UploadRequestHeaders(
                authorization=storage_record.token,
                file_size=new_file_size
            ).dict(by_alias=True)
        )
