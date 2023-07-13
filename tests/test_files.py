from unittest.mock import AsyncMock, patch

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from api.db import models
from api.schemas.storage_api import StorageSpaceResponse
from tests.base_tests import (
    TestWithClient,
    TestWithStreamIteratorMixin,
    add_test_authentication,
)


@add_test_authentication(
    ("get", "/files/download"),
    ("post", "/files/upload"),
    ("delete", "/files/delete"),
)
class TestFiles(TestWithClient, TestWithStreamIteratorMixin):
    async def test_download_file_not_exists(self):
        response = self.authorized_request(
            "get", "/files/download", headers={"path": "/nonexistent_path"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("aiohttp.ClientSession.get")
    async def test_download_file(self, request_mock: AsyncMock):
        storage_response = request_mock.return_value.__aenter__.return_value
        storage_response.status = status.HTTP_200_OK
        storage_response.content.iter_any = self.stream_generator
        response = self.authorized_request(
            "get", "/files/download", headers={"path": "/a1/f1"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.text
        self.assertEqual(content, self.stream_content)

    @patch("aiohttp.ClientSession.post")
    async def test_upload_file(self, request_mock: AsyncMock):
        storage_response = StorageSpaceResponse(
            used=500, capacity=self.settings.session_storage_max_size
        )
        request_mock.return_value.__aenter__.return_value.status = status.HTTP_200_OK
        request_mock.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=storage_response.dict()
        )
        file_size = 100
        response = self.authorized_request(
            "post",
            "/files/upload",
            data=iter("data"),
            headers={"path": "/a1/b1/c1/file", "file-size": str(file_size)},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        created_file_record = (
            await self.session.scalars(
                select(models.FileRecord)
                .options(joinedload(models.FileRecord.storage))
                .where(models.FileRecord.full_path == "/a1/b1/c1/file")
            )
        ).first()
        self.assertIsNotNone(created_file_record)
        self.assertEqual(created_file_record.size, file_size)
        self.assertEqual(created_file_record.storage.used_space, storage_response.used)
