from unittest.mock import AsyncMock, patch

from fastapi import status

from api.db import crud
from tests.base_tests import (
    TestWithRegisteredKey,
    TestWithStreamIteratorMixin,
    add_test_authentication,
)


@add_test_authentication("/files/upload")
class TestFiles(TestWithRegisteredKey, TestWithStreamIteratorMixin):
    @patch("aiohttp.ClientSession")
    async def test_download_file_not_exists(self, request_mock: AsyncMock):
        request_mock.return_value.__aenter__.return_value.get.return_value.status = 200
        request_mock.return_value.__aenter__.return_value.get.return_value.content = (
            self.stream_generator
        )
        folder_record = await crud.create_folders_recursively(
            self.session, self.key_record, "/folder"
        )
        file_record = await crud.create_file_record(
            self.session, folder_record, "filename", self.storage_record, 100
        )
        await crud.update_record(self.session, file_record)
        response = self.authorized_request(
            "get", "/files/download", headers={"path": "/nonexistent_path"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("aiohttp.ClientSession.get")
    async def test_download_file(self, request_mock: AsyncMock):
        storage_response = request_mock.return_value.__aenter__.return_value
        storage_response.status = 200
        storage_response.content.iter_any = self.stream_generator
        folder_record = await crud.create_folders_recursively(
            self.session, self.key_record, "/folder"
        )
        file_record = await crud.create_file_record(
            self.session, folder_record, "filename", self.storage_record, 100
        )
        await crud.update_record(self.session, file_record)
        await self.session.commit()
        response = self.authorized_request(
            "get", "/files/download", headers={"path": "/folder/filename"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.text
        self.assertEqual(content, self.stream_content)
