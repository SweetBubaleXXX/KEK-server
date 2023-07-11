from asyncio import sleep
from unittest.mock import AsyncMock, patch

from fastapi import status
from pydantic import BaseModel
from sqlalchemy import select

from api.db import crud, models
from api.exceptions.core import StorageResponseError
from api.schemas.storage_api import (
    StorageRequestHeaders,
    StorageSpaceResponse,
    UploadRequestHeaders,
)
from api.utils.storage import StorageClient
from tests.base_tests import TestWithClient, TestWithStreamIteratorMixin


class TestStorageClient(TestWithClient, TestWithStreamIteratorMixin):
    @patch("aiohttp.ClientSession.get")
    async def test_download_file_response_error(self, request_mock: AsyncMock):
        storage_response = request_mock.return_value.__aenter__.return_value
        storage_response.content.iter_any = self.stream_generator
        storage_response.status = status.HTTP_500_INTERNAL_SERVER_ERROR
        file_record = (
            await self.session.scalars(
                select(models.FileRecord).where(models.FileRecord.full_path == "/a1/f1")
            )
        ).one()
        with self.assertRaises(StorageResponseError):
            stream_iterator = StorageClient.download_file(file_record)
            await anext(aiter(stream_iterator))

    @patch("aiohttp.ClientSession.post")
    async def test_upload_existing_file(self, request_mock: AsyncMock):
        storage_response = StorageSpaceResponse(
            used=400, capacity=self.settings.session_storage_max_size
        )
        self.__set_request_mock_value(request_mock, storage_response)
        storage_record = (
            await self.session.scalars(select(models.StorageRecord))
        ).one()
        existing_file_record = (
            await self.session.scalars(
                select(models.FileRecord).where(models.FileRecord.full_path == "/a1/f1")
            )
        ).one()
        prev_modified = existing_file_record.last_modified
        new_file_size = 100
        storage_client = StorageClient(
            self.session, await self.key_record, storage_record
        )
        stream_generator = self.stream_generator()
        await sleep(0.1)
        file_record = await storage_client.upload_file(
            existing_file_record.full_path, new_file_size, stream_generator
        )
        self.assertEqual(storage_record.used_space, storage_response.used)
        self.assertEqual(file_record.size, new_file_size)
        self.assertGreater(file_record.last_modified, prev_modified)
        request_mock.assert_called_once_with(
            f"/file/{file_record.id}",
            data=stream_generator,
            headers=UploadRequestHeaders(
                authorization=storage_record.token, file_size=new_file_size
            ).dict(by_alias=True),
        )

    @patch("aiohttp.ClientSession.post")
    async def test_upload_new_file(self, request_mock: AsyncMock):
        storage_response = StorageSpaceResponse(
            used=400, capacity=self.settings.session_storage_max_size
        )
        self.__set_request_mock_value(request_mock, storage_response)
        storage_record = (
            await self.session.scalars(select(models.StorageRecord))
        ).one()
        storage_client = StorageClient(
            self.session, await self.key_record, storage_record
        )
        file_size = 100
        stream_generator = self.stream_generator()
        file_record = await storage_client.upload_file(
            "/a1/b1/c1/f", file_size, stream_generator
        )
        self.assertEqual(storage_record.used_space, storage_response.used)
        self.assertEqual(file_record.storage_id, storage_record.id)
        self.assertEqual(
            (await file_record.awaitable_attrs.folder).full_path, "/a1/b1/c1"
        )
        request_mock.assert_called_once_with(
            f"/file/{file_record.id}",
            data=stream_generator,
            headers=UploadRequestHeaders(
                authorization=storage_record.token, file_size=file_size
            ).dict(by_alias=True),
        )

    @patch("aiohttp.ClientSession.delete")
    async def test_delete_file(self, request_mock: AsyncMock):
        storage_response = StorageSpaceResponse(
            used=400, capacity=self.settings.session_storage_max_size
        )
        self.__set_request_mock_value(request_mock, storage_response)
        storage_record = (
            await self.session.scalars(select(models.StorageRecord))
        ).one()
        file_record = (
            await self.session.scalars(
                select(models.FileRecord).where(models.FileRecord.full_path == "/a1/f1")
            )
        ).one()
        storage_client = StorageClient(
            self.session, await self.key_record, storage_record
        )
        await storage_client.delete_file(file_record)
        file_in_db = (
            await self.session.scalars(
                select(models.FileRecord).where(models.FileRecord.full_path == "/a1/f1")
            )
        ).first()
        self.assertIsNone(file_in_db)
        request_mock.assert_called_once_with(
            f"/file/{file_record.id}",
            headers=StorageRequestHeaders(
                authorization=storage_record.token,
            ).dict(by_alias=True),
        )

    @patch("aiohttp.ClientSession.delete")
    async def test_delete_folder(self, request_mock: AsyncMock):
        storage_response = StorageSpaceResponse(used=0, capacity=10000000)
        self.__set_request_mock_value(request_mock, storage_response)
        folder_record = (
            await self.session.scalars(
                select(models.FolderRecord).where(
                    models.FolderRecord.full_path == "/a1"
                )
            )
        ).one()
        await StorageClient.delete_folder(self.session, folder_record)
        found_folder_record = (
            await self.session.scalars(
                select(models.FolderRecord).where(
                    models.FolderRecord.full_path == "/a1"
                )
            )
        ).first()
        self.assertIsNone(found_folder_record)
        for folder_path in ("b1", "b2", "b1/c1"):
            found_folder_record = (
                await self.session.scalars(
                    select(models.FolderRecord).where(
                        models.FolderRecord.full_path == f"/a1/{folder_path}"
                    )
                )
            ).first()
        self.assertIsNone(found_folder_record)
        for file_path in ("f1", "f2", "f3", "b1/f1", "b2/f2"):
            found_file_record = (
                await self.session.scalars(
                    select(models.FileRecord).where(
                        models.FileRecord.full_path == f"/a1/{file_path}"
                    )
                )
            ).first()
            self.assertIsNone(found_file_record)

    def __set_request_mock_value(self, mock: AsyncMock, response: BaseModel):
        mock.return_value.__aenter__.return_value.status = status.HTTP_200_OK
        mock.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=response.dict()
        )
