from fastapi import APIRouter, Depends, Header
from fastapi.requests import Request
from sqlalchemy.orm import Session

from ..db import crud, models
from ..dependencies import get_db, get_key_record, verify_token
from ..exceptions import exceptions
from ..utils.path_utils import split_head_and_tail
from ..utils.storage import get_available_storage
from ..utils.storage_api import delete_file, redirect_file

router = APIRouter(tags=["files"], dependencies=[Depends(verify_token)])


@router.post("/upload")
async def upload_file(
    request: Request,
    path: str = Header(),
    file_size: int = Header(),
    key_record: models.KeyRecord = Depends(get_key_record),
    db: Session = Depends(get_db)
):
    available_storage = get_available_storage(db, key_record, file_size)

    file_record = crud.find_file(db, owner=key_record, full_path=path)
    old_storage_id = None
    if file_record is None:
        folder_name, filename = split_head_and_tail(path)
        folder_record = crud.find_folder(db, owner=key_record, full_path=folder_name)
        if folder_record is None:
            raise exceptions.NotExists(detail="Parent folder doesn't exist")
        file_record = crud.create_file_record(db, folder_record, filename,
                                              available_storage, file_size)
    else:
        old_storage_id = file_record.storage_id
        file_record.storage = available_storage
        file_record.size = file_size
    await redirect_file(request.stream(), file_record, available_storage)
    if old_storage_id is not None:
        old_storage = crud.get_storage(db, old_storage_id)
        await delete_file(file_record, old_storage)
    crud.update_record(db, file_record)
    crud.update_record(db, available_storage)
