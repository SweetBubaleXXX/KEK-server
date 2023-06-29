import pytest

from api.db import models


@pytest.fixture
def storage_record(request: pytest.FixtureRequest):
    request.cls.storage_record = models.StorageRecord(
        id="storage_id", url="https://storage", token="token"
    )


@pytest.fixture
def stream_generator(request: pytest.FixtureRequest):
    request.cls.stream_generator = lambda: (yield from b"data")
