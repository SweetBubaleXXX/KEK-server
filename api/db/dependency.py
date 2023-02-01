from sqlalchemy.orm import sessionmaker


def create_get_db_dependency(session_local: sessionmaker):
    def get_db():
        db_session = session_local()
        try:
            yield db_session
        finally:
            db_session.close()
    return get_db
