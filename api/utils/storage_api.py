from typing import AsyncIterator
from urllib.parse import urljoin

import aiohttp

from ..db import models
from ..schemas.storage_api import StorageSpaceResponse, UploadRequestHeaders


async def redirect_file(stream: AsyncIterator[bytes],
                        file_record: models.FileRecord,
                        storage: models.StorageRecord):
    url = urljoin(storage.url, file_record.id)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=stream, headers=UploadRequestHeaders(
            file_size=file_record.size
        ).dict(by_alias=True)) as res:
            await __update_storage_space(res, storage)


async def delete_file(file_record: models.FileRecord, storage: models.StorageRecord):
    url = urljoin(storage.url, file_record.id)
    async with aiohttp.ClientSession() as session:
        async with session.delete(url) as res:
            await __update_storage_space(res, storage)


async def __update_storage_space(res: aiohttp.ClientResponse, storage: models.StorageRecord):
    storage_space = StorageSpaceResponse.parse_obj(await res.json())
    storage.used_space = storage_space.used
