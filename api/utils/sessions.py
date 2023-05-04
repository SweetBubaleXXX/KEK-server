from abc import ABCMeta, abstractmethod
from uuid import UUID, uuid4


class BaseSessionStorage(dict[str, UUID], metaclass=ABCMeta):
    @abstractmethod
    def add(self, key_id: str) -> UUID:
        pass


class SessionStorage(BaseSessionStorage):
    def add(self, key_id: str) -> UUID:
        self[key_id] = uuid4()
        return self[key_id]


def create_session_dependency():
    def get_session():
        return session_storage

    session_storage = SessionStorage()
    return get_session
