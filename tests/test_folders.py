from fastapi import status

from tests.base_tests import TestWithClient, TestWithKeyRecord, add_test_authentication


@add_test_authentication("/folders/mkdir")
class TestFoldres(TestWithKeyRecord, TestWithClient):
    def test_create_folder(self): ...
