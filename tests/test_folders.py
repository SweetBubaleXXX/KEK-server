import unittest

from fastapi.testclient import TestClient

from api.db import engine, models
from api.main import app
from tests.setup_test_env import (setup_config, setup_database,
                                  teardown_database)


class TestFolders(unittest.TestCase):
    def setUp(self):
        self.settings = setup_config()
        self.engine, self.session = setup_database(engine.Base)
        self.client = TestClient(app)

    def test_list_empty_folder(self):
        pass

    def tearDown(self):
        teardown_database(engine.Base, self.engine)
