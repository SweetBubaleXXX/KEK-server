from base64 import b64encode

from fastapi import status
from httpx import Response
from KEK.hybrid import PrivateKEK

from api.db import models
from tests.base_tests import TestWithClientMixin, TestWithDatabase


class TestRegistration(TestWithDatabase, TestWithClientMixin):
    def test_empty_request(self):
        response = self.client.post("/register", json={})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_invalid_public_key(self):
        key = PrivateKEK.generate()
        response = self.client.post(
            "/register", json={"key_id": key.key_id.hex(), "public_key": "invalid_key"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_key_id(self):
        key = PrivateKEK.generate()
        response = self.client.post(
            "/register",
            json={
                "key_id": "invalid_key_id",
                "public_key": key.public_key.serialize().decode("utf-8"),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized(self):
        key = PrivateKEK.generate()
        response = self.client.post("/register", json=self.__public_key_info(key))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_registration_required(self):
        key = PrivateKEK.generate()
        response = self.client.post("/register", json=self.__public_key_info(key))
        self.assertFalse(response.json().get("registration_required"))

    def test_invalid_token(self):
        key = PrivateKEK.generate()
        response = self.client.post("/register", json=self.__public_key_info(key))
        self.assertIsNotNone(response.json().get("token"))
        response = self.client.post(
            "/register",
            json=self.__public_key_info(key),
            headers={"Signed-Token": "invalid_token"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.json().get("token"))

    def test_token(self):
        key = PrivateKEK.generate()
        response = self.__register_key(key)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_key_in_db(self):
        key = PrivateKEK.generate()
        self.__register_key(key)
        key_record = (
            self.session.query(models.KeyRecord).filter_by(id=key.key_id.hex()).first()
        )
        self.assertEqual(
            key_record.public_key, key.public_key.serialize().decode("utf-8")
        )

    def test_root_folder_creation(self):
        key = PrivateKEK.generate()
        self.__register_key(key)
        root_folder = (
            self.session.query(models.FolderRecord)
            .filter_by(owner_id=key.key_id.hex(), full_path=models.ROOT_PATH)
            .first()
        )
        self.assertEqual(root_folder.owner.id, key.key_id.hex())

    def __public_key_info(self, key: PrivateKEK) -> dict[str, str]:
        return {
            "key_id": key.key_id.hex(),
            "public_key": key.public_key.serialize().decode("utf-8"),
        }

    def __register_key(self, key: PrivateKEK) -> Response:
        response = self.client.post("/register", json=self.__public_key_info(key))
        token = response.json().get("token")
        signed_token = b64encode(key.sign(token.encode("utf-8")))
        return self.client.post(
            "/register",
            json=self.__public_key_info(key),
            headers={"Signed-Token": signed_token.decode()},
        )
