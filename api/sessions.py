from uuid import UUID, uuid4


class SessionStorage(dict[str, UUID]):
    def add(self, key_id: str) -> UUID:
        self[key_id] = uuid4()
        return self[key_id]


def create_session_dependency():
    session_storage = SessionStorage()

    def get_session():
        return session_storage

    return get_session
