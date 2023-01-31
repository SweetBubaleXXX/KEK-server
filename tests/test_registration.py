import unittest

from fastapi.testclient import TestClient
from fastapi import status
from KEK.hybrid import PrivateKEK

from api.db import engine, models
from api.main import app
from tests.setup_test_env import (setup_config, setup_database,
                                  teardown_database)


class TestRegistration(unittest.TestCase):
    def setUp(self):
        self.settings = setup_config()
        self.engine, self.session = setup_database(engine.Base)
        self.client = TestClient(app)

    def _public_key_info(self, key: PrivateKEK) -> dict:
        return {
            "key_id": key.key_id.hex(),
            "public_key": key.public_key.serialize().decode("utf-8")
        }

    def test_empty_request(self):
        response = self.client.post("/register", json={})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_invalid_public_key(self):
        key = PrivateKEK.generate()
        response = self.client.post("/register", json={
            "key_id": key.key_id.hex(),
            "public_key": "invalid_key"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_key_id(self):
        key = PrivateKEK.generate()
        response = self.client.post("/register", json={
            "key_id": "invalid_key_id",
            "public_key": key.public_key.serialize().decode("utf-8")
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized(self):
        key = PrivateKEK.generate()
        response = self.client.post("/register", json=self._public_key_info(key))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_registration_required(self):
        key = PrivateKEK.generate()
        response = self.client.post("/register", json=self._public_key_info(key))
        self.assertFalse(response.json().get("registration_required"))

    def test_invalid_token(self):
        key = PrivateKEK.generate()
        response = self.client.post("/register", json=self._public_key_info(key))
        self.assertIsNotNone(response.json().get("token"))
        response = self.client.post("/register", json=self._public_key_info(key),
                                    headers={"Signed-Token": "invalid_token"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def tearDown(self):
        teardown_database(engine.Base, self.engine)
