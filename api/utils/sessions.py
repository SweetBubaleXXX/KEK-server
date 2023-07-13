from collections.abc import MutableMapping
from threading import Lock
from uuid import UUID, uuid4

from cachetools import TTLCache

from .. import config


class BaseSessionStorage(MutableMapping[str, UUID]):
    def __init__(self) -> None:
        self._lock = Lock()

    @property
    def lock(self) -> Lock:
        return self._lock

    def add(self, key_id: str) -> UUID:
        self[key_id] = uuid4()
        return self[key_id]


class SessionStorage(BaseSessionStorage, TTLCache):
    def __init__(self, maxsize: int, ttl: int) -> None:
        super().__init__()
        TTLCache.__init__(self, maxsize, ttl)


def create_session_dependency():
    def get_session():
        return session_storage

    session_storage = SessionStorage(
        config.settings.SESSION_STORAGE_MAX_SIZE, config.settings.SESSION_TTL
    )
    return get_session
