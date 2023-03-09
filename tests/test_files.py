import asynctest
from fastapi import status

from api.db import models
from tests.base_tests import TestWithRegisteredKey, add_test_authentication


@add_test_authentication("/files/upload")
class TestFiles(TestWithRegisteredKey):
    @asynctest.patch("aiohttp.ClientSession.post")
    def test_upload(self, mock: asynctest.CoroutineMock):
        mock.return_value.__aenter__.return_value.json = asynctest.CoroutineMock(
            return_value={
                "used": 200
            }
        )
        file_content = b"File content"
        response = self.authorized_request("post", "/files/upload", headers={
            "path": "/file",
            "file-size": len(file_content)
        }, data=file_content)
