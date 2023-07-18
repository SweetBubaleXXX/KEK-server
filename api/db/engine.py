from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .. import config

engine = create_async_engine(
    config.settings.DATABASE_URL,
    isolation_level=config.settings.DATABASE_ISOLATION_LEVEL,
)
async_session = async_sessionmaker(engine, expire_on_commit=False)
