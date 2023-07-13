from KEK.hybrid import PrivateKEK
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api import config
from api.app import app
from api.db import engine as db
from api.db import models
from api.db.dependency import create_get_db_dependency
from api.dependencies import get_db

KEY = PrivateKEK.generate()
KEY_ID = KEY.key_id.hex()
FILE_SIZE = 10

test_settings = config.Settings(_env_file=".config.test")  # type: ignore[call-arg]


def setup_config() -> config.Settings:
    config.settings = test_settings
    return config.settings


async def setup_database() -> AsyncSession:
    db.engine = create_async_engine(test_settings.DATABASE_URL)
    async with db.engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    app.dependency_overrides[get_db] = create_get_db_dependency(
        async_sessionmaker(db.engine, expire_on_commit=False)
    )
    session = AsyncSession(db.engine)
    return session


async def teardown_database(session: AsyncSession):
    await session.close()
    async with db.engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)


async def setup_data(session: AsyncSession, settings: config.Settings):
    key_record = models.KeyRecord(
        id=KEY_ID,
        public_key=KEY.public_key.serialize().decode("utf-8"),
        storage_size_limit=settings.USER_STORAGE_SIZE_LIMIT,
        is_activated=settings.USER_IS_ACTIVATED_DEFAULT,
    )
    storage_record = models.StorageRecord(
        id="storage_id",
        url="http://storage",
        token="storage_token",
        capacity=500,
        priority=1,
    )
    root_folder = models.FolderRecord(owner=key_record, name="/", full_path="/")
    for folder_name in ("a1", "a2", "a3"):
        folder_record = models.FolderRecord(
            owner=key_record,
            parent_folder=root_folder,
            name=folder_name,
            full_path=f"/{folder_name}",
        )
        for filename in ("f1", "f2", "f3", "f4"):
            file_record = models.FileRecord(
                folder=folder_record,
                storage=storage_record,
                filename=filename,
                full_path=f"{folder_record.full_path}/{filename}",
                size=FILE_SIZE,
            )
            folder_record.files.append(file_record)
        for child_folder_name in ("b1", "b2"):
            child_folder = models.FolderRecord(
                owner=key_record,
                parent_folder=folder_record,
                name=child_folder_name,
                full_path=f"{folder_record.full_path}/{child_folder_name}",
            )
            for filename in ("f1", "f2", "f3"):
                file_record = models.FileRecord(
                    folder=child_folder,
                    storage=storage_record,
                    filename=filename,
                    full_path=f"{child_folder.full_path}/{filename}",
                    size=FILE_SIZE,
                )
            child_folder.files.append(file_record)
            child_folder.child_folders.append(
                models.FolderRecord(
                    owner=key_record,
                    name="c1",
                    full_path=f"{child_folder.full_path}/c1",
                )
            )
            folder_record.child_folders.append(child_folder)
        root_folder.child_folders.append(folder_record)
    session.add_all((key_record, root_folder, storage_record))
    await session.commit()
