import unittest
from base64 import b64encode
from typing import AsyncGenerator, Literal, Type

from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response

from api.app import app
from api.db import models
from tests.setup_test_env import (
    setup_config,
    setup_database,
    teardown_database,
    setup_data,
    KEY,
    KEY_ID,
)

RequestMethod = Literal["get", "post", "delete"]


class TestWithDatabase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.settings = setup_config()
        self.session = await setup_database()
        await setup_data(self.session, self.settings)

    async def asyncTearDown(self):
        await teardown_database(self.session)

    @property
    async def key_record(self) -> models.KeyRecord:
        key_record = await self.session.get(models.KeyRecord, KEY_ID)
        assert key_record
        return key_record


class TestWithClient(TestWithDatabase):
    def setUp(self):
        super().setUp()
        self.client = TestClient(app)

    def authorized_request(
        self, method: RequestMethod, *args, headers: dict | None = None, **kwargs
    ) -> Response:
        if headers is None:
            headers = {}
        headers = headers | {"key-id": KEY_ID}
        response = self.request(method, *args, headers=headers, **kwargs)
        token = response.json()["token"]
        signed_token = b64encode(KEY.sign(token.encode("utf-8")))
        headers = headers | {"Signed-Token": signed_token}
        return self.request(method, *args, headers=headers, **kwargs)

    def request(self, method: RequestMethod, *args, **kwargs) -> Response:
        match method.casefold():
            case "get":
                return self.client.get(*args, **kwargs)
            case "post":
                return self.client.post(*args, **kwargs)
            case "delete":
                return self.client.delete(*args, **kwargs)
            case _:
                raise ValueError("Method not recognized")


class TestWithStreamIteratorMixin:
    stream_content = "Content"

    async def stream_generator(self, *args, **kwargs) -> AsyncGenerator:
        for chunk in self.stream_content:
            yield chunk


def test_authentication(*urls: tuple[RequestMethod, str]):
    def decorator(cls: Type[TestWithClient]):
        def test_unauthorized(self: TestWithClient):
            for method, path in urls:
                response = self.request(method, path, headers={"Key-Id": KEY_ID})
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        def test_registration_required_false(self: TestWithClient):
            for method, path in urls:
                response = self.request(method, path, headers={"Key-Id": KEY_ID})
                self.assertFalse(response.json().get("registration_required"))

        def test_registration_required_true(self: TestWithClient):
            for method, path in urls:
                response = self.request(method, path, headers={"Key-Id": "unknown_id"})
                self.assertTrue(response.json().get("registration_required"))

        def test_invalid_token(self: TestWithClient):
            for method, path in urls:
                response = self.request(method, path, headers={"Key-Id": KEY_ID})
                self.assertIsNotNone(response.json().get("token"))
                response = self.request(
                    method,
                    path,
                    headers={"Key-Id": KEY_ID, "Signed-Token": "invalid_token"},
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        setattr(cls, "test_unauthorized", test_unauthorized)
        setattr(
            cls, "test_registration_required_false", test_registration_required_false
        )
        setattr(cls, "test_registration_required_true", test_registration_required_true)
        setattr(cls, "test_invallid_token", test_invalid_token)
        return cls

    return decorator
