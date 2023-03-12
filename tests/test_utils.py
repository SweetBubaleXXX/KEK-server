from unittest import IsolatedAsyncioTestCase, mock

from api.db import models
from api.utils.file_upload import redirect_file


class TestFileUploadUtils(IsolatedAsyncioTestCase):
    @mock.patch("aiohttp.ClientSession.post")
    async def test_redirect_file_response(self, request_mock: mock.AsyncMock):
        def _stream_generator():
            yield b"value"

        expected_value = 500
        request_mock.return_value.__aenter__.return_value.json = mock.AsyncMock(return_value={
            "used": expected_value
        })
        storage_record = models.StorageRecord()
        file_record = models.FileRecord()
        await redirect_file(_stream_generator(), file_record, storage_record)
        request_mock.assert_called()
        self.assertEqual(storage_record.used_space, expected_value)
