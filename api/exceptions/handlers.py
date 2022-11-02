from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from ..dependencies import get_session
from ..schemas import BaseRequest, DetailedTokenResponse
from . import exceptions


def authentication_required_handler(request: BaseRequest,
                                    exc: exceptions.AuthenticationRequired):
    session_storage = get_session()
    token = session_storage.add(request.key_id)
    # return DetailedTokenResponse(
    #     token,
    #     detail=exc.detail
    # )
    return JSONResponse(content=jsonable_encoder(
        {
            "detail": exc.detail,
            "token": token
        }
    ), status_code=exc.status_code, headers=exc.headers)
