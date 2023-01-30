from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from ..config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()
