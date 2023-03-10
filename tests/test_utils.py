import asynctest

from api.db import models
from api.utils.file_upload import redirect_file


class TestFileUploadUtils(asynctest.TestCase):
    @asynctest.patch("aiohttp.ClientSession.post")
    async def test_redirect_file_response(self, mock: asynctest.CoroutineMock):
        def _stream_generator():
            yield b"value"

        expected_value = 500
        mock.return_value.__aenter__.return_value.json = asynctest.CoroutineMock(return_value={
            "used": expected_value
        })
        storage_record = models.StorageRecord()
        file_record = models.FileRecord()
        await redirect_file(_stream_generator(), file_record, storage_record)
        self.assertEqual(storage_record.used_space, expected_value)
