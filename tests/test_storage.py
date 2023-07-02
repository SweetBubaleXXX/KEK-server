from asyncio import sleep
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from pydantic import BaseModel

from api.db import crud
from api.exceptions.core import StorageResponseError
from api.schemas.storage_api import (
    StorageRequestHeaders,
    StorageSpaceResponse,
    UploadRequestHeaders,
)
from api.utils.storage import StorageClient
from tests.base_tests import TestWithRegisteredKey, TestWithStreamIteratorMixin


class TestStorageClient(
    IsolatedAsyncioTestCase, TestWithRegisteredKey, TestWithStreamIteratorMixin
):
    @patch("aiohttp.ClientSession.get")
    async def test_download_file_response_error(self, request_mock: AsyncMock):
        storage_response = request_mock.return_value.__aenter__.return_value
        storage_response.content.iter_any = self.stream_generator
        storage_response.status = 500
        folder_record = crud.create_folders_recursively(
            self.session, self.key_record, "/folder"
        )
        file_record = crud.create_file_record(
            self.session, folder_record, "filename", self.storage_record, 100
        )
        crud.update_record(self.session, file_record)
        with self.assertRaises(StorageResponseError):
            stream_iterator = StorageClient.download_file(file_record)
            await anext(aiter(stream_iterator))

    @patch("aiohttp.ClientSession.post")
    async def test_upload_existing_file(self, request_mock: AsyncMock):
        storage_response = StorageSpaceResponse(used=10, capacity=10000000)
        self.__set_request_mock_value(request_mock, storage_response)
        folder_record = crud.create_folders_recursively(
            self.session, self.key_record, "/folder"
        )
        existing_file_record = crud.create_file_record(
            self.session,
            folder_record,
            "filename",
            self.storage_record,
            storage_response.used,
        )
        crud.update_record(self.session, existing_file_record)
        prev_modified = existing_file_record.last_modified

        storage_client = StorageClient(
            self.session, self.key_record, self.storage_record
        )
        new_file_size = 200
        stream_generator = self.stream_generator()
        await sleep(0.1)
        file_record = await storage_client.upload_file(
            existing_file_record.full_path, new_file_size, stream_generator
        )
        crud.update_record(self.session, self.storage_record)
        crud.update_record(self.session, file_record)

        self.assertEqual(self.storage_record.used_space, storage_response.used)
        self.assertEqual(file_record.size, new_file_size)
        self.assertGreater(file_record.last_modified, prev_modified)
        request_mock.assert_called_once_with(
            f"/file/{file_record.id}",
            data=stream_generator,
            headers=UploadRequestHeaders(
                authorization=self.storage_record.token, file_size=new_file_size
            ).dict(by_alias=True),
        )

    @patch("aiohttp.ClientSession.post")
    async def test_upload_new_file(self, request_mock: AsyncMock):
        storage_response = StorageSpaceResponse(used=10, capacity=10000000)
        self.__set_request_mock_value(request_mock, storage_response)
        folder_record = crud.create_folders_recursively(
            self.session, self.key_record, "/folder"
        )
        crud.update_record(self.session, folder_record)

        storage_client = StorageClient(
            self.session, self.key_record, self.storage_record
        )
        file_size = 200
        stream_generator = self.stream_generator()
        file_record = await storage_client.upload_file(
            "/folder/filename", file_size, stream_generator
        )
        crud.update_record(self.session, self.storage_record)
        crud.update_record(self.session, file_record)

        self.assertEqual(self.storage_record.used_space, storage_response.used)
        self.assertEqual(file_record.storage_id, self.storage_record.id)
        self.assertEqual(file_record.folder.id, folder_record.id)
        request_mock.assert_called_once_with(
            f"/file/{file_record.id}",
            data=stream_generator,
            headers=UploadRequestHeaders(
                authorization=self.storage_record.token, file_size=file_size
            ).dict(by_alias=True),
        )

    @patch("aiohttp.ClientSession.delete")
    async def test_delete_file(self, request_mock: AsyncMock):
        storage_response = StorageSpaceResponse(used=0, capacity=10000000)
        self.__set_request_mock_value(request_mock, storage_response)
        folder_record = crud.create_folders_recursively(
            self.session, self.key_record, "/folder"
        )
        file_record = crud.create_file_record(
            self.session, folder_record, "filename", self.storage_record, 100
        )
        crud.update_record(self.session, file_record)

        storage_client = StorageClient(
            self.session, self.key_record, self.storage_record
        )
        await storage_client.delete_file(file_record)
        crud.update_record(self.session, folder_record)

        self.assertListEqual(folder_record.files, [])
        request_mock.assert_called_once_with(
            f"/file/{file_record.id}",
            headers=StorageRequestHeaders(
                authorization=self.storage_record.token,
            ).dict(by_alias=True),
        )

    @patch("aiohttp.ClientSession.delete")
    async def test_delete_folder(self, request_mock: AsyncMock):
        storage_response = StorageSpaceResponse(used=0, capacity=10000000)
        self.__set_request_mock_value(request_mock, storage_response)
        parent_folder = crud.create_folders_recursively(
            self.session, self.key_record, "/parent_folder"
        )
        folder_record = crud.create_folders_recursively(
            self.session, self.key_record, "/parent_folder/folder"
        )
        filenames = ("a", "b", "c")
        for name in filenames:
            file_record = crud.create_file_record(
                self.session, folder_record, name, self.storage_record, 1
            )
            crud.update_record(self.session, file_record)
        crud.update_record(self.session, parent_folder)

        await StorageClient.delete_folder(self.session, parent_folder)

        found_folder_record = crud.find_folder(self.session, full_path="/parent_folder")
        self.assertIsNone(found_folder_record)
        for name in filenames:
            found_file_record = crud.find_file(
                self.session, self.key_record, full_path=f"/parent_folder/folder/{name}"
            )
            self.assertIsNone(found_file_record)

    def __set_request_mock_value(self, mock: AsyncMock, response: BaseModel):
        mock.return_value.__aenter__.return_value.status = 200
        mock.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=response.dict()
        )
