from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response

from ..schemas.authentication import DetailedTokenResponse
from . import client, core


def registration_required_handler(_: Request, exc: client.AuthenticationException):
    return JSONResponse(
        content=jsonable_encoder(
            DetailedTokenResponse(
                token=exc.session, detail=exc.detail, registration_required=True
            )
        ),
        status_code=exc.status_code,
        headers=exc.headers,
    )


def authentication_required_handler(_: Request, exc: client.AuthenticationException):
    return JSONResponse(
        content=jsonable_encoder(
            DetailedTokenResponse(token=exc.session, detail=exc.detail)
        ),
        status_code=exc.status_code,
        headers=exc.headers,
    )


def no_available_storage_handler(_: Request, exc: core.NoAvailableStorage):
    return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


def storage_response_error_handler(_: Request, exc: core.StorageResponseError):
    return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
