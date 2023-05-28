from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status

from api.db import crud, models
from api.schemas.storage_api import (StorageRequestHeaders, StorageSpaceResponse,
                                     UploadRequestHeaders)
from api.utils.storage import StorageClient
from tests.base_tests import TestWithRegisteredKey


@pytest.mark.usefixtures("stream_generator")
@pytest.mark.usefixtures("storage_record")
class TestStorageClient(IsolatedAsyncioTestCase, TestWithRegisteredKey):
    @patch("aiohttp.ClientSession")
    async def test_download_file(self, request_mock: AsyncMock):
        request_mock.return_value.__aenter__.return_value.get.return_value.status = 200
        request_mock.return_value.__aenter__.return_value.get.return_value.content = self.stream_generator
        folder_record = models.FolderRecord(
            owner=self.key_record,
            name="folder",
            full_path="folder"
        )
        file_record = models.FileRecord(
            folder=folder_record,
            storage=self.storage_record,
            filename="filename",
            full_path="folder/filename",
            size=100
        )
        crud.update_record(self.session, file_record)

        response = await StorageClient.download_file(file_record)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("aiohttp.ClientSession.post")
    async def test_upload_existing_file(self, request_mock: AsyncMock):
        storage_response = StorageSpaceResponse(
            used=10,
            capacity=10000000
        )
        self.__set_request_mock_value(request_mock, storage_response)
        folder_record = models.FolderRecord(
            owner=self.key_record,
            name="folder",
            full_path="folder"
        )
        existing_file_record = models.FileRecord(
            folder=folder_record,
            storage=self.storage_record,
            filename="filename",
            full_path="folder/filename",
            size=0
        )
        crud.update_record(self.session, existing_file_record)
        prev_modified = existing_file_record.last_modified

        storage_client = StorageClient(self.session, self.key_record, self.storage_record)
        new_file_size = 200
        file_record = await storage_client.upload_file(
            existing_file_record.full_path,
            new_file_size,
            self.stream_generator
        )
        crud.update_record(self.session, self.storage_record)
        crud.update_record(self.session, file_record)

        self.assertEqual(self.storage_record.used_space, storage_response.used)
        self.assertEqual(file_record.size, new_file_size)
        self.assertGreater(file_record.last_modified, prev_modified)
        request_mock.assert_called_once_with(
            f'/file/{file_record.id}',
            data=self.stream_generator,
            headers=UploadRequestHeaders(
                authorization=self.storage_record.token,
                file_size=new_file_size
            ).dict(by_alias=True)
        )

    @patch("aiohttp.ClientSession.post")
    async def test_upload_new_file(self, request_mock: AsyncMock):
        storage_response = StorageSpaceResponse(
            used=10,
            capacity=10000000
        )
        self.__set_request_mock_value(request_mock, storage_response)
        folder_record = models.FolderRecord(
            owner=self.key_record,
            name="folder",
            full_path="folder"
        )
        crud.update_record(self.session, folder_record)

        storage_client = StorageClient(self.session, self.key_record, self.storage_record)
        file_size = 200
        file_record = await storage_client.upload_file(
            "folder/filename",
            file_size,
            self.stream_generator
        )
        crud.update_record(self.session, self.storage_record)
        crud.update_record(self.session, file_record)

        self.assertEqual(self.storage_record.used_space, storage_response.used)
        self.assertEqual(file_record.storage_id, self.storage_record.id)
        self.assertEqual(file_record.folder.id, folder_record.id)
        request_mock.assert_called_once_with(
            f'/file/{file_record.id}',
            data=self.stream_generator,
            headers=UploadRequestHeaders(
                authorization=self.storage_record.token,
                file_size=file_size
            ).dict(by_alias=True)
        )

    @patch("aiohttp.ClientSession.delete")
    async def test_delete_file(self, request_mock: AsyncMock):
        storage_response = StorageSpaceResponse(
            used=0,
            capacity=10000000
        )
        self.__set_request_mock_value(request_mock, storage_response)
        folder_record = models.FolderRecord(
            owner=self.key_record,
            name="folder",
            full_path="folder"
        )
        file_record = models.FileRecord(
            folder=folder_record,
            storage=self.storage_record,
            filename="filename",
            full_path="folder/filename",
            size=100
        )
        crud.update_record(self.session, file_record)

        storage_client = StorageClient(self.session, self.key_record, self.storage_record)
        await storage_client.delete_file(file_record)
        crud.update_record(self.session, folder_record)

        self.assertListEqual(folder_record.files, [])
        request_mock.assert_called_once_with(
            f'/file/{file_record.id}',
            headers=StorageRequestHeaders(
                authorization=self.storage_record.token,
            ).dict(by_alias=True)
        )
