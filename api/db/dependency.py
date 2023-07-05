from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def create_get_db_dependency(async_session: async_sessionmaker[AsyncSession]):
    async def get_db():
        async with async_session.begin() as session:
            yield session

    return get_db
