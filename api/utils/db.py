from sqlalchemy.orm import sessionmaker


def create_get_db_dependency(sessionmaker: sessionmaker):
    def get_db():
        db_session = sessionmaker()
        try:
            yield db_session
        finally:
            db_session.close()
    return get_db
