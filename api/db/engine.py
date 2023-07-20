from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .. import config

engine = create_async_engine(
    config.settings.DATABASE_URL,
    isolation_level=config.settings.DATABASE_ISOLATION_LEVEL,
)
async_session = async_sessionmaker(engine, expire_on_commit=False)


def create_get_db_dependency(async_session: async_sessionmaker[AsyncSession]):
    async def get_db():
        async with async_session.begin() as session:
            yield session

    return get_db
