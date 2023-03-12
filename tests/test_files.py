from fastapi import status

from api.db import models
from tests.base_tests import TestWithRegisteredKey, add_test_authentication


@add_test_authentication("/files/upload")
class TestFiles(TestWithRegisteredKey):
    ...
