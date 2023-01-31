from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .. import config

engine = create_engine(config.settings.database_url)
SessionLocal = sessionmaker(engine)
Base = declarative_base()
