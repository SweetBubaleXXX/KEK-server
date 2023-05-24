from typing import AsyncIterator, Type

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

    async def parse_storage_space(self, response: ClientResponse):
        if not response.ok:
            raise core.StorageResponseError(response)
        storage_info = storage_api.StorageSpaceResponse.parse_obj(await response.json())
        self._storage.used_space = storage_info.used


class DeleteFileHandler(BaseHandler):
    async def delete_from_storage(self, file_record: models.FileRecord):
        async with aiohttp.ClientSession(self._storage.url) as session:
            async with session.delete(f'/file/{file_record.id}',
                                      headers=storage_api.StorageRequestHeaders(
                                          authorization=self._storage.token
                                      ).dict(by_alias=True)) as res:
                await self.parse_storage_space(res)

    async def __call__(self, file_record: models.FileRecord):
        await self.delete_from_storage(file_record)


class BaseUploadFileHandler(BaseHandler):
    async def upload_stream(self, stream: AsyncIterator[bytes], file_record: models.FileRecord):
        async with aiohttp.ClientSession(self._storage.url) as session:
            async with session.post(f'/file/{file_record.id}',
                                    data=stream,
                                    headers=storage_api.UploadRequestHeaders(
                                        authorization=self._storage.token,
                                        file_size=file_record.size
                                    ).dict(by_alias=True)) as res:
                await self.parse_storage_space(res)


class UploadExistingFileRecordHandler(BaseUploadFileHandler):
    async def __call__(self,
                       file_record: models.FileRecord,
                       file_size: int,
                       stream: AsyncIterator[bytes]):
        old_storage_id = file_record.storage_id
        file_record.storage = self._storage
        file_record.size = file_size
        self._session.add(file_record)
        await self.upload_stream(stream, file_record)
        if old_storage_id != self._storage.id:
            await self.__delete_from_old_storage(file_record, old_storage_id)
        return file_record

    async def __delete_from_old_storage(self, file_record: models.FileRecord, old_storage_id: str):
        old_storage = crud.get_storage(self._session, old_storage_id)
        if old_storage is None:
            raise core.StorageNotFound
        delete_handler = DeleteFileHandler(self._session, self._client, old_storage)
        await delete_handler.delete_from_storage(file_record)
        self._session.add(old_storage)


class UploadNewFileRecordHandler(BaseUploadFileHandler):
    async def __call__(self,
                       full_path: str,
                       file_size: int,
                       stream: AsyncIterator[bytes]):
        folder_name, filename = split_head_and_tail(full_path)
        folder_record = crud.find_folder(self._session, owner=self._client, full_path=folder_name)
        if folder_record is None:
            raise client.NotExists(detail="Parent folder doesn't exist")
        file_record = crud.create_file_record(self._session, folder_record, filename,
                                              self._storage, file_size)
        self._session.add(file_record)
        await self.upload_stream(stream, file_record)
        return file_record


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

    @staticmethod
    async def download_file(session: aiohttp.ClientSession,
                            file_record: models.FileRecord) -> aiohttp.StreamReader:
        async with session.get(f'/file/{file_record.id}',
                               headers=storage_api.StorageRequestHeaders(
                                   authorization=file_record.storage.token
                               ).dict(by_alias=True)) as res:
            if not res.ok:
                raise core.StorageResponseError(res)
            return res.content

    async def upload_file(self,
                          full_path: str,
                          file_size: int,
                          stream: AsyncIterator[bytes]):
        file_record = self._session.query(models.FileRecord).filter_by(
            full_path=full_path
        ).join(models.FileRecord.folder).filter_by(
            owner=self._client,
        ).first()
        if file_record is None:
            file_record = await self.__create_handler(UploadNewFileRecordHandler)(
                full_path,
                file_size,
                stream
            )
        else:
            file_record = await self.__create_handler(UploadExistingFileRecordHandler)(
                file_record,
                file_size,
                stream
            )
        self._session.add(self._storage)
        return file_record

    async def delete_file(self, file_record: models.FileRecord):
        await self.__create_handler(DeleteFileHandler)(file_record)
        self._session.delete(file_record)

    def __create_handler(self, handler_cls: Type[BaseHandler]):
        return handler_cls(
            self._session,
            self._client,
            self._storage
        )
