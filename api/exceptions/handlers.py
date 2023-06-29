from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response

from ..schemas.authentication import DetailedTokenResponse
from . import client, core


def registration_required_handler(_: Request, exc: client.RegistrationRequired):
    return JSONResponse(content=jsonable_encoder(
        DetailedTokenResponse(
            token=exc.token,
            detail=exc.detail,
            registration_required=True
        )
    ), status_code=exc.status_code, headers=exc.headers)


def authentication_required_handler(_: Request, exc: client.AuthenticationRequired):
    return JSONResponse(content=jsonable_encoder(
        DetailedTokenResponse(
            token=exc.token,
            detail=exc.detail
        )
    ), status_code=exc.status_code, headers=exc.headers)


def no_available_storage_handler(_: Request, exc: core.NoAvailableStorage):
    return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
