from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response

from ..dependencies import get_session
from ..schemas.authentication import DetailedTokenResponse
from . import client, core


def registration_required_handler(_: Request, exc: client.RegistrationRequired):
    session_storage = get_session()
    token = session_storage.add(exc.key_id)
    return JSONResponse(content=jsonable_encoder(
        DetailedTokenResponse(
            token=token,
            detail=exc.detail,
            registration_required=True
        )
    ), status_code=exc.status_code, headers=exc.headers)


def authentication_required_handler(_: Request, exc: client.AuthenticationRequired):
    session_storage = get_session()
    token = session_storage.add(exc.key_id)
    return JSONResponse(content=jsonable_encoder(
        DetailedTokenResponse(
            token=token,
            detail=exc.detail
        )
    ), status_code=exc.status_code, headers=exc.headers)


def no_available_storage_handler(_: Request, exc: core.NoAvailableStorage):
    return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
