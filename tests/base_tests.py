import unittest
from typing import Type

from fastapi import status
from fastapi.testclient import TestClient
from KEK.hybrid import PrivateKEK

from api.app import app
from api.db import models
from tests.setup_test_env import (setup_config, setup_database,
                                  teardown_database)


def add_test_authentication(url):
    def decorator(cls: Type[TestWithKeyRecordAndClient]):
        def test_unauthorized(self: TestWithKeyRecordAndClient):
            response = self.client.post(url, headers={
                "Key-Id": self.key_record.id
            })
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        def test_registration_required_false(self: TestWithKeyRecordAndClient):
            response = self.client.post(url, headers={
                "Key-Id": self.key_record.id
            })
            self.assertFalse(response.json().get("registration_required"))

        def test_registration_required_true(self: TestWithKeyRecordAndClient):
            response = self.client.post(url, headers={
                "Key-Id": "unknown_id"
            })
            self.assertTrue(response.json().get("registration_required"))

        def test_invalid_token(self: TestWithKeyRecordAndClient):
            response = self.client.post(url, headers={
                "Key-Id": self.key_record.id
            })
            self.assertIsNotNone(response.json().get("token"))
            response = self.client.post(url, headers={
                "Key-Id": self.key_record.id,
                "Signed-Token": "invalid_token"
            })
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        setattr(cls, "test_unauthorized", test_unauthorized)
        setattr(cls, "test_registration_required_false", test_registration_required_false)
        setattr(cls, "test_registration_required_true", test_registration_required_true)
        setattr(cls, "test_invallid_token", test_invalid_token)
        return cls

    return decorator


class TestWithDatabase(unittest.TestCase):
    def setUp(self):
        self.settings = setup_config()
        self.session = setup_database()

    def tearDown(self):
        teardown_database(self.session)


class TestWithKeyRecord(TestWithDatabase):
    def setUp(self):
        super().setUp()
        self.key = PrivateKEK.generate()
        self.key_record = self._add_key_to_db()

    def _add_key_to_db(self) -> models.KeyRecord:
        key_record = models.KeyRecord(
            id=self.key.key_id.hex(),
            public_key=self.key.public_key.serialize().decode("utf-8")
        )
        self.session.add(key_record)
        self.session.commit()
        self.session.refresh(key_record)
        return key_record


class TestWithClient():
    client = TestClient(app)


class TestWithKeyRecordAndClient(TestWithKeyRecord, TestWithClient):
    pass
