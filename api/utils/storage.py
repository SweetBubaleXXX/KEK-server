from typing import AsyncIterator, Type
from urllib.parse import urljoin

import aiohttp
from sqlalchemy.orm import Session

from ..db import crud, models
from .. import exceptions
from ..schemas.storage_api import StorageSpaceResponse, UploadRequestHeaders
from .path_utils import split_head_and_tail


class BaseHandler:
    def __init__(self, db: Session, client: models.KeyRecord, storage: models.StorageRecord):
        self._session = db
        self._client = client
        self._storage = storage

    def get_url(self, file_record: models.FileRecord) -> str:
        return urljoin(self._storage.url, file_record.id)


class DeleteFileHandler(BaseHandler):
    async def delete_from_storage(self, file_record: models.FileRecord):
        url = self.get_url(file_record.id)
        async with aiohttp.ClientSession() as session:
            async with session.delete(url) as res:
                if not res.ok:
                    raise Exception
                storage_space = StorageSpaceResponse.parse_obj(await res.json())
                self._storage.used_space = storage_space.used

    async def __call__(self, file_record: models.FileRecord):
        pass


class UploadFileHandler(BaseHandler):
    async def upload_stream(self, stream: AsyncIterator[bytes], file_record: models.FileRecord):
        url = self.get_url(file_record.id)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=stream, headers=UploadRequestHeaders(
                file_size=file_record.size
            ).dict(by_alias=True)) as res:
                if not res.ok:
                    raise Exception
                storage_space = StorageSpaceResponse.parse_obj(await res.json())
                self._storage.used_space = storage_space.used


class UploadExistingFileRecordHandler(UploadFileHandler):
    async def __call__(self, file_record: models.FileRecord,
                       file_size: int, stream: AsyncIterator[bytes]):
        old_storage_id = file_record.storage_id
        file_record.storage = self._storage
        file_record.size = file_size
        await self.upload_stream(stream, file_record)
        old_storage = crud.get_storage(self._session, old_storage_id)
        if old_storage is None:
            raise exceptions.core.StorageNotFound
        delete_handler = DeleteFileHandler(self._session, self._client, old_storage)
        await delete_handler.delete_from_storage(file_record)


class UploadNewFileRecordHandler(UploadFileHandler):
    async def __call__(self, full_path: str, file_size: int, stream: AsyncIterator[bytes]):
        folder_name, filename = split_head_and_tail(full_path)
        folder_record = crud.find_folder(self._session, owner=self._client, full_path=folder_name)
        if folder_record is None:
            raise exceptions.client.NotExists(detail="Parent folder doesn't exist")
        file_record = crud.create_file_record(self._session, folder_record, filename,
                                              self._storage, file_size)
        await self.upload_stream(stream, file_record)


class StorageClient:
    def __init__(self, db: Session, client: models.KeyRecord, storage: models.StorageRecord):
        self._session = db
        self._client = client
        self._storage = storage

    @property
    def storage(self) -> models.StorageRecord:
        return self._storage

    @property
    def client(self) -> models.KeyRecord:
        return self._client

    async def upload_file(self, full_path: str, file_size: int, stream: AsyncIterator[bytes]):
        existing_record = crud.find_file(self._session, owner=self._client, full_path=full_path)
        if existing_record is None:
            return await self.__create_handler(UploadNewFileRecordHandler)(
                full_path,
                file_size,
                stream
            )
        return await self.__create_handler(UploadExistingFileRecordHandler)(
            existing_record,
            file_size,
            stream
        )

    def __create_handler(self, handler_cls: Type[BaseHandler]):
        return handler_cls(
            self._session,
            self._storage,
            self._client
        )
