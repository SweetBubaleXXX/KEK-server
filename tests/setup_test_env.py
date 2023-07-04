from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from api import config
from api.app import app
from api.db import engine as db
from api.db.models import Base
from api.db.dependency import create_get_db_dependency
from api.dependencies import get_db

test_settings = config.Settings(_env_file=".config.test")


def setup_config() -> config.Settings:
    config.settings = test_settings
    return config.settings


async def setup_database() -> AsyncSession:
    db.engine = create_async_engine(test_settings.database_url, echo=True)
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = create_get_db_dependency(
        async_sessionmaker(db.engine)
    )
    session = AsyncSession(db.engine)
    return session


async def teardown_database(session: AsyncSession):
    await session.close()
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
