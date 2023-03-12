from unittest import IsolatedAsyncioTestCase, mock

from api.db import models
from api.schemas.storage_api import StorageSpaceResponse
from api.utils.storage_api import delete_file, redirect_file


class TestFileUploadUtils(IsolatedAsyncioTestCase):
    @mock.patch("aiohttp.ClientSession.post")
    async def test_redirect_file_response(self, request_mock: mock.AsyncMock):
        def __stream_generator():
            yield b"value"

        expected_value = 500
        self.__set_request_mock_value(request_mock, expected_value)
        storage_record = models.StorageRecord()
        file_record = models.FileRecord(size=0)
        await redirect_file(__stream_generator(), file_record, storage_record)
        request_mock.assert_called()
        self.assertEqual(storage_record.used_space, expected_value)

    @mock.patch("aiohttp.ClientSession.delete")
    async def test_delete_file_response(self, request_mock: mock.AsyncMock):
        expected_value = 500
        self.__set_request_mock_value(request_mock, expected_value)
        storage_record = models.StorageRecord()
        file_record = models.FileRecord(size=0)
        await delete_file(file_record, storage_record)
        request_mock.assert_called()
        self.assertEqual(storage_record.used_space, expected_value)

    def __set_request_mock_value(self, request_mock: mock.AsyncMock, expected_value: int):
        request_mock.return_value.__aenter__.return_value.json = mock.AsyncMock(
            return_value=StorageSpaceResponse(capacity=0, used=expected_value).dict()
        )
