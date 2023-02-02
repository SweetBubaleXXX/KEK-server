import unittest
from base64 import b64encode

from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
from KEK.hybrid import PrivateKEK

from api.app import app
from api.db import models
from tests.setup_test_env import (setup_config, setup_database,
                                  teardown_database)


class TestRegistration(unittest.TestCase):
    def setUp(self):
        self.settings = setup_config()
        self.session = setup_database()
        self.client = TestClient(app)
        self.key = PrivateKEK.generate()
        self.key_record = self._register_key(self.key)

    def test_create_folder(): ...

    def tearDown(self):
        teardown_database(self.session)

    def _activate_key(self, key_record: models.KeyRecord) -> models.KeyRecord:
        key_record.is_activated = True
        self.session.add(key_record)
        self.session.commit()
        self.session.flush()
        return key_record

    def _register_key(self, key: PrivateKEK) -> models.KeyRecord:
        key_record = models.KeyRecord(
            id=key.key_id.hex(),
            public_key=key.public_key.serialize().decode("utf-8")
        )
        self.session.add(key_record)
        self.session.commit()
        self.session.refresh(key_record)
        return key_record
