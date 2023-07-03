from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .. import config

engine = create_engine(config.settings.database_url)
SessionLocal = sessionmaker(engine)
