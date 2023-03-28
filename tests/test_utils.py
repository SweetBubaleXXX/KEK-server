from unittest.mock import AsyncMock, patch

from api.db import models
from api.schemas.storage_api import StorageSpaceResponse
from api.utils.storage import StorageClient
from tests.base_tests import TestWithRegisteredKey


class TestStorageClient(TestWithRegisteredKey):
    @patch("aiohttp.ClientSession.post")
    async def test_upload_new_file(self, request_mock: AsyncMock):
        request_mock.return_value.__aenter__.return_value.ok = True
        request_mock.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=StorageSpaceResponse(
                used=10,
                capacity=100
            ))
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
        storage_client = StorageClient(self.session, self.key_record, storage_record)
        await storage_client.upload_file("folder/filename", 0, lambda: (yield b""))
