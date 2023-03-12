from typing import AsyncIterator
from urllib.parse import urljoin

import aiohttp

from ..db import models
from ..schemas.storage_api import UploadRequestHeaders, UploadResponse


async def redirect_file(stream: AsyncIterator[bytes],
                        file_record: models.FileRecord,
                        storage: models.StorageRecord):
    url = urljoin(storage.url, file_record.id)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=stream, headers=UploadRequestHeaders(
            file_size=file_record.size
        ).dict(by_alias=True)) as resp:
            storage_space = UploadResponse.parse_obj(await resp.json())
            storage.used_space = storage_space.used
