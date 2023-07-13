from typing import AsyncIterator, Type, TypeVar

import aiohttp
from aiohttp.client import ClientResponse
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import crud, models
from ..exceptions import client, core
from ..schemas import storage_api
from .path_utils import split_head_and_tail


class BaseHandler:
    def __init__(
        self,
        db: AsyncSession,
        key_record: models.KeyRecord,
        storage: models.StorageRecord,
    ):
        self._session = db
        self._client = key_record
        self._storage = storage

    @staticmethod
    def validate_response(response: ClientResponse):
        if response.status != status.HTTP_200_OK:
            raise core.StorageResponseError(response)

    async def parse_storage_space(self, response: ClientResponse):
        storage_info = storage_api.StorageSpaceResponse.parse_obj(await response.json())
        self._storage.used_space = storage_info.used


class DeleteFileHandler(BaseHandler):
    async def delete_from_storage(self, file_record: models.FileRecord):
        async with aiohttp.ClientSession(self._storage.url) as session:
            async with session.delete(
                f"/file/{file_record.id}",
                headers=storage_api.StorageRequestHeaders(
                    authorization=self._storage.token
                ).dict(by_alias=True),
            ) as res:
                self.validate_response(res)
                await self.parse_storage_space(res)

    async def __call__(self, file_record: models.FileRecord):
        await self.delete_from_storage(file_record)


class BaseUploadFileHandler(BaseHandler):
    async def upload_stream(
        self, stream: AsyncIterator[bytes], file_record: models.FileRecord
    ):
        async with aiohttp.ClientSession(self._storage.url) as session:
            async with session.post(
                f"/file/{file_record.id}",
                data=stream,
                headers=storage_api.UploadRequestHeaders(
                    authorization=self._storage.token, file_size=str(file_record.size)
                ).dict(by_alias=True),
            ) as res:
                await self.parse_storage_space(res)


class UploadExistingFileRecordHandler(BaseUploadFileHandler):
    async def __call__(
        self,
        file_record: models.FileRecord,
        file_size: int,
        stream: AsyncIterator[bytes],
    ) -> models.FileRecord:
        old_storage_id = file_record.storage_id
        file_record.storage = self._storage
        file_record.size = file_size
        file_record.update_timestamp()
        await self.upload_stream(stream, file_record)
        self._session.add(file_record)
        try:
            if old_storage_id != self._storage.id:
                await self.__delete_from_old_storage(file_record, old_storage_id)
        finally:
            return file_record

    async def __delete_from_old_storage(
        self, file_record: models.FileRecord, old_storage_id: str
    ):
        old_storage = await self._session.get(models.StorageRecord, old_storage_id)
        if old_storage is None:
            raise core.StorageNotFound()
        delete_handler = DeleteFileHandler(self._session, self._client, old_storage)
        await delete_handler.delete_from_storage(file_record)
        self._session.add(old_storage)


class UploadNewFileRecordHandler(BaseUploadFileHandler):
    async def __call__(
        self, full_path: str, file_size: int, stream: AsyncIterator[bytes]
    ) -> models.FileRecord:
        folder_name, filename = split_head_and_tail(full_path)
        folder_record = await crud.find_folder(
            self._session, owner=self._client, full_path=folder_name
        )
        if folder_record is None:
            raise client.NotExists(detail="Parent folder doesn't exist")
        file_record = await crud.create_file_record(
            self._session, folder_record, filename, self._storage, file_size
        )
        await self.upload_stream(stream, file_record)
        self._session.add(file_record)
        return file_record


T = TypeVar("T", bound=BaseHandler)


class StorageClient:
    def __init__(
        self,
        db: AsyncSession,
        key_record: models.KeyRecord,
        storage: models.StorageRecord,
    ):
        self._session = db
        self._client = key_record
        self._storage = storage

    @property
    def session(self) -> AsyncSession:
        return self._session

    @property
    def client(self) -> models.KeyRecord:
        return self._client

    @property
    def storage(self) -> models.StorageRecord:
        return self._storage

    @staticmethod
    async def download_file(file_record: models.FileRecord) -> AsyncIterator[bytes]:
        async with aiohttp.ClientSession(
            (await file_record.awaitable_attrs.storage).url
        ) as session:
            async with session.get(
                f"/file/{file_record.id}",
                headers=storage_api.StorageRequestHeaders(
                    authorization=(await file_record.awaitable_attrs.storage).token
                ).dict(by_alias=True),
            ) as res:
                BaseHandler.validate_response(res)
                async for chunk in res.content.iter_any():
                    yield chunk

    @staticmethod
    async def delete_folder(db: AsyncSession, folder_record: models.FolderRecord):
        files_to_delete = await db.stream_scalars(
            select(models.FileRecord)
            .join(models.FileRecord.folder)
            .where(
                models.FolderRecord.owner_id == folder_record.owner_id,
                models.FileRecord.full_path.startswith(folder_record.full_path),
            )
        )
        async for file_record in files_to_delete:
            storage_client = StorageClient(
                db,
                await folder_record.awaitable_attrs.owner,
                await file_record.awaitable_attrs.storage,
            )
            await storage_client.delete_file(file_record)
        await db.delete(folder_record)
        await db.flush()

    async def upload_file(
        self, full_path: str, file_size: int, stream: AsyncIterator[bytes]
    ) -> models.FileRecord:
        file_record = await crud.find_file(
            self._session, self._client, full_path=full_path
        )
        if file_record is None:
            file_record = await self.__create_handler(UploadNewFileRecordHandler)(
                full_path, file_size, stream
            )
        else:
            file_record = await self.__create_handler(UploadExistingFileRecordHandler)(
                file_record, file_size, stream
            )
        self._session.add(self._storage)
        await self._session.flush()
        return file_record

    async def delete_file(self, file_record: models.FileRecord):
        await self.__create_handler(DeleteFileHandler)(file_record)
        await self._session.delete(file_record)
        await self._session.flush()

    def __create_handler(self, handler_cls: Type[T]) -> T:
        return handler_cls(self._session, self._client, self._storage)
