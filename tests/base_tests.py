import unittest
from base64 import b64encode
from typing import AsyncGenerator, Literal, Type

from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
from KEK.hybrid import PrivateKEK

from api.app import app
from api.db import models
from tests.setup_test_env import setup_config, setup_database, teardown_database

RequestMethod = Literal["get", "post", "delete"]


class TestWithDatabase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = setup_config()

    async def asyncSetUp(self):
        self.session = await setup_database()

    async def asyncTearDown(self):
        await teardown_database(self.session)


class TestWithKeyRecord(TestWithDatabase):
    key = PrivateKEK.generate()

    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.key_record = await self.__add_key_to_db()

    async def __add_key_to_db(self) -> models.KeyRecord:
        key_record = models.KeyRecord(
            id=self.key.key_id.hex(),
            public_key=self.key.public_key.serialize().decode("utf-8"),
        )
        self.session.add(key_record)
        await self.session.commit()
        await self.session.refresh(key_record)
        return key_record


class TestWithClientMixin:
    client = TestClient(app)


class TestWithStreamIteratorMixin:
    stream_content = "content"

    async def stream_generator(self, *args, **kwargs) -> AsyncGenerator:
        for chunk in self.stream_content:
            yield chunk


class TestWithRegisteredKey(TestWithKeyRecord, TestWithClientMixin):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        root_folder = models.FolderRecord(
            owner=self.key_record, name=models.ROOT_PATH, full_path=models.ROOT_PATH
        )
        self.storage_record = models.StorageRecord(
            id="storage_id", url="http://storage", token="token"
        )
        self.session.add(root_folder)
        self.session.add(self.storage_record)
        await self.session.commit()
        await self.session.refresh(self.key_record)

    def authorized_request(
        self, method: RequestMethod, *args, headers: dict | None = None, **kwargs
    ):
        if headers is None:
            headers = {}
        headers = headers | {"key-id": self.key_record.id}
        response = self.__request(method, *args, headers=headers, **kwargs)
        token = response.json().get("token")
        signed_token = b64encode(self.key.sign(token.encode("utf-8")))
        headers = headers | {"Signed-Token": signed_token}
        return self.__request(method, *args, headers=headers, **kwargs)

    def __request(self, method: RequestMethod, *args, **kwargs) -> Response:
        match method.casefold():
            case "get":
                return self.client.get(*args, **kwargs)
            case "post":
                return self.client.post(*args, **kwargs)
            case "delete":
                return self.client.delete(*args, **kwargs)
            case _:
                raise ValueError("Method not recognized")


def add_test_authentication(url):
    def decorator(cls: Type[TestWithRegisteredKey]):
        def test_unauthorized(self: TestWithRegisteredKey):
            response = self.client.post(url, headers={"Key-Id": self.key_record.id})
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        def test_registration_required_false(self: TestWithRegisteredKey):
            response = self.client.post(url, headers={"Key-Id": self.key_record.id})
            self.assertFalse(response.json().get("registration_required"))

        def test_registration_required_true(self: TestWithRegisteredKey):
            response = self.client.post(url, headers={"Key-Id": "unknown_id"})
            self.assertTrue(response.json().get("registration_required"))

        def test_invalid_token(self: TestWithRegisteredKey):
            response = self.client.post(url, headers={"Key-Id": self.key_record.id})
            self.assertIsNotNone(response.json().get("token"))
            response = self.client.post(
                url,
                headers={"Key-Id": self.key_record.id, "Signed-Token": "invalid_token"},
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
