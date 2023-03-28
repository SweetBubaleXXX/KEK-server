from typing import AsyncIterator, Type
from urllib.parse import urljoin

import aiohttp
from aiohttp.client import ClientResponse
from sqlalchemy.orm import Session

from ..db import crud, models
from ..exceptions import client, core
from ..schemas import storage_api
from .path_utils import split_head_and_tail


class BaseHandler:
    def __init__(self, db: Session, key_record: models.KeyRecord, storage: models.StorageRecord):
        self._session = db
        self._client = key_record
        self._storage = storage

    def get_url(self, file_record: models.FileRecord) -> str:
        return urljoin(self._storage.url, file_record.id)

    async def parse_storage_space(self, response: ClientResponse):
        storage_info = storage_api.StorageSpaceResponse.parse_obj(await response.json())
        self._storage.used_space = storage_info.used


class DeleteFileHandler(BaseHandler):
    async def delete_from_storage(self, file_record: models.FileRecord):
        url = self.get_url(file_record.id)
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=storage_api.StorageRequestHeaders(
                authorization=self._storage.token
            ).dict(by_alias=True)) as res:
                if not res.ok:
                    raise core.StorageResponseError(res)
                await self.parse_storage_space(res)

    async def __call__(self, file_record: models.FileRecord):
        await self.delete_from_storage(file_record)


class UploadFileHandler(BaseHandler):
    async def upload_stream(self, stream: AsyncIterator[bytes], file_record: models.FileRecord):
        url = self.get_url(file_record.id)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=stream, headers=storage_api.UploadRequestHeaders(
                authorization=self._storage.token,
                file_size=file_record.size
            ).dict(by_alias=True)) as res:
                if not res.ok:
                    raise core.StorageResponseError(res)
                await self.parse_storage_space(res)


class UploadExistingFileRecordHandler(UploadFileHandler):
    async def __call__(self, file_record: models.FileRecord,
                       file_size: int, stream: AsyncIterator[bytes]):
        old_storage_id = file_record.storage_id
        file_record.storage = self._storage
        file_record.size = file_size
        self._session.add(file_record)
        await self.upload_stream(stream, file_record)
        if old_storage_id != self._storage.id:
            await self.__delete_from_old_storage(file_record, old_storage_id)

    async def __delete_from_old_storage(self, file_record: models.FileRecord, old_storage_id: str):
        old_storage = crud.get_storage(self._session, old_storage_id)
        if old_storage is None:
            raise core.StorageNotFound
        delete_handler = DeleteFileHandler(self._session, self._client, old_storage)
        await delete_handler.delete_from_storage(file_record)
        self._session.add(old_storage)


class UploadNewFileRecordHandler(UploadFileHandler):
    async def __call__(self, full_path: str, file_size: int, stream: AsyncIterator[bytes]):
        folder_name, filename = split_head_and_tail(full_path)
        folder_record = crud.find_folder(self._session, owner=self._client, full_path=folder_name)
        if folder_record is None:
            raise client.NotExists(detail="Parent folder doesn't exist")
        file_record = crud.create_file_record(self._session, folder_record, filename,
                                              self._storage, file_size)
        self._session.add(file_record)
        await self.upload_stream(stream, file_record)


class StorageClient:
    def __init__(self, db: Session, key_record: models.KeyRecord, storage: models.StorageRecord):
        self._session = db
        self._client = key_record
        self._storage = storage

    @property
    def session(self) -> Session:
        return self._session

    @property
    def client(self) -> models.KeyRecord:
        return self._client

    @property
    def storage(self) -> models.StorageRecord:
        return self._storage

    async def upload_file(self, full_path: str, file_size: int, stream: AsyncIterator[bytes]):
        existing_record = crud.find_file(self._session, owner=self._client, full_path=full_path)
        if existing_record is None:
            await self.__create_handler(UploadNewFileRecordHandler)(
                full_path,
                file_size,
                stream
            )
        else:
            await self.__create_handler(UploadExistingFileRecordHandler)(
                existing_record,
                file_size,
                stream
            )
        self._session.add(self._storage)

    async def delete_file(self, full_path):
        file_record = crud.find_file(self._session, owner=self._client, full_path=full_path)
        self.__create_handler(DeleteFileHandler)(file_record)

    def __create_handler(self, handler_cls: Type[BaseHandler]):
        return handler_cls(
            self._session,
            self._client,
            self._storage
        )
