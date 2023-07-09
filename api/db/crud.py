import posixpath

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import config
from ..utils.path_utils import split_head_and_tail, split_into_components
from . import models


async def __update_child_full_paths(folder: models.FolderRecord):
    for file in await folder.awaitable_attrs.files:
        file.full_path = posixpath.join(folder.full_path, file.filename)
    for child_folder in await folder.awaitable_attrs.child_folders:
        child_folder.full_path = posixpath.join(folder.full_path, child_folder.name)
        await __update_child_full_paths(child_folder)


async def update_record(db: AsyncSession, record: models.Record) -> models.Record:
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def get_key_by_id(db: AsyncSession, key_id: str) -> models.KeyRecord | None:
    return await db.get(models.KeyRecord, key_id)


async def add_key(
    db: AsyncSession,
    key_id: str,
    public_key: str,
    storage_limit: int | None = None,
    is_activated: bool = False,
) -> models.KeyRecord:
    key_record = models.KeyRecord(
        id=key_id,
        public_key=public_key,
        storage_size_limit=storage_limit or config.settings.user_storage_size_limit,
        is_activated=is_activated or config.settings.user_is_activated_default,
    )
    return await update_record(db, key_record)


async def return_or_create_root_folder(
    db: AsyncSession, key_record: models.KeyRecord
) -> models.FolderRecord:
    existing_folder_record = (
        await db.scalars(
            select(models.FolderRecord).where(
                models.FolderRecord.owner == key_record,
                models.FolderRecord.full_path == models.ROOT_PATH,
            )
        )
    ).first()
    if existing_folder_record:
        return existing_folder_record
    folder_record = models.FolderRecord(
        owner=key_record, name=models.ROOT_PATH, full_path=models.ROOT_PATH
    )
    return await update_record(db, folder_record)


async def create_child_folder(
    db: AsyncSession, parent_folder: models.FolderRecord, name: str
) -> models.FolderRecord:
    child_folder = models.FolderRecord(
        owner=await parent_folder.awaitable_attrs.owner,
        parent_folder=parent_folder,
        name=name,
        full_path=posixpath.join(parent_folder.full_path, name),
    )
    return await update_record(db, child_folder)


async def create_folders_recursively(
    db: AsyncSession, key_record: models.KeyRecord, folder_path: str
) -> models.FolderRecord:
    current_folder = await return_or_create_root_folder(db, key_record)
    path_components = split_into_components(folder_path)
    for folder_name in path_components:
        existing_child = next(
            filter(
                lambda current_folder: current_folder.name == folder_name,
                await current_folder.awaitable_attrs.child_folders,
            ),
            None,
        )
        if existing_child:
            current_folder = existing_child
            continue
        current_folder = await create_child_folder(db, current_folder, folder_name)
    return await update_record(db, current_folder)


async def rename_folder(
    db: AsyncSession, folder: models.FolderRecord, new_name: str
) -> models.FolderRecord:
    folder.name = new_name
    parent_path, _ = split_head_and_tail(folder.full_path)
    folder.full_path = posixpath.join(parent_path, new_name)
    await __update_child_full_paths(folder)
    return await update_record(db, folder)


async def move_folder(
    db: AsyncSession,
    folder: models.FolderRecord,
    destination_folder: models.FolderRecord,
) -> models.FolderRecord:
    folder.parent_folder = destination_folder
    folder.full_path = posixpath.join(destination_folder.full_path, folder.name)
    await __update_child_full_paths(folder)
    return await update_record(db, folder)


async def find_folder(db: AsyncSession, **filters) -> models.FolderRecord | None:
    return (await db.scalars(select(models.FolderRecord).filter_by(**filters))).first()


async def folder_exists(db: AsyncSession, **filters) -> bool:
    return bool(
        (await db.scalars(select(models.FolderRecord).filter_by(**filters))).first()
    )


async def find_file(
    db: AsyncSession, owner: models.KeyRecord, **filters
) -> models.FileRecord | None:
    return (
        await db.scalars(
            select(models.FileRecord)
            .filter_by(**filters)
            .join(models.FileRecord.folder)
            .where(models.FolderRecord.owner == owner)
        )
    ).first()


async def file_exists(db: AsyncSession, owner: models.KeyRecord, **filters) -> bool:
    return bool(await find_file(db, owner, **filters))


async def item_in_folder(
    db: AsyncSession, name: str, folder: models.FolderRecord
) -> bool:
    existing_folder_found = await folder_exists(db, parent_folder=folder, name=name)
    existing_file_found = await file_exists(
        db, owner=await folder.awaitable_attrs.owner, folder=folder, filename=name
    )
    return existing_file_found or existing_folder_found


async def create_file_record(
    db: AsyncSession,
    folder: models.FolderRecord,
    filename: str,
    storage: models.StorageRecord,
    size: int,
) -> models.FileRecord:
    file_record = models.FileRecord(
        folder=folder,
        storage=storage,
        filename=filename,
        full_path=posixpath.join(folder.full_path, filename),
        size=size,
    )
    return await update_record(db, file_record)


async def get_storage(db: AsyncSession, storage_id: str) -> models.StorageRecord | None:
    return await db.get(models.StorageRecord, storage_id)


async def calculate_used_storage(db: AsyncSession, key_record: models.KeyRecord) -> int:
    return (
        await db.scalar(
            select(func.sum(models.FileRecord.size))
            .join(models.FileRecord.folder)
            .where(models.FolderRecord.owner == key_record)
        )
    ) or 0
