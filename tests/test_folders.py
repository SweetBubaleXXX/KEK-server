
from fastapi.testclient import TestClient

from api.app import app
from tests.setup_test_env import TestWithKeyRecord


class TestFoldres(TestWithKeyRecord):
    def setUp(self):
        super().setUp()
        self.client = TestClient(app)

    def test_create_folder(): ...
