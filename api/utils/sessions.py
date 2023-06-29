from abc import ABCMeta, abstractmethod
from collections import UserDict
from collections.abc import MutableMapping
from threading import Lock
from uuid import UUID, uuid4


class BaseSessionStorage(MutableMapping[str, UUID], metaclass=ABCMeta):
    def __init__(self) -> None:
        super().__init__()
        self._lock = Lock()

    @property
    def lock(self) -> Lock:
        return self._lock

    @abstractmethod
    def add(self, key_id: str) -> UUID:
        pass


class SessionStorage(BaseSessionStorage, UserDict[str, UUID]):
    def add(self, key_id: str) -> UUID:
        self[key_id] = uuid4()
        return self[key_id]


def create_session_dependency():
    def get_session():
        return session_storage

    session_storage = SessionStorage()
    return get_session
