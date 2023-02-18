from fastapi import status

from tests.base_tests import (TestWithKeyRecordAndClient,
                              add_test_authentication)


@add_test_authentication("/folders/mkdir")
class TestFoldres(TestWithKeyRecordAndClient):
    def test_create_folder(self): ...
