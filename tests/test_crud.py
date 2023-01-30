import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from api.db import Base, crud
from tests.setup_test_config import setup_config


class TestCrud(unittest.TestCase):
    def setUp(self):
        setup_config()
        self.engine = create_engine("sqlite:///:memory:")
        self.session = Session(self.engine)
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        Base.metadata.drop_all(self.engine)
