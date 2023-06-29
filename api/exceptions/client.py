from uuid import UUID

from fastapi import status
from fastapi.exceptions import HTTPException

HEADERS = dict[str, str] | None


class AuthenticationException(HTTPException):
    def __init__(
        self,
        session: UUID,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail="Error during authentication",
        headers: HEADERS = None,
    ):
        self.session = session
        super().__init__(status_code, detail, headers)


class AuthenticationRequired(AuthenticationException):
    def __init__(
        self,
        session: UUID,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        detail="Token authentication required",
        headers: HEADERS = None,
    ):
        super().__init__(session, status_code, detail, headers)


class AuthenticationFailed(AuthenticationException):
    def __init__(
        self,
        session: UUID,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail="Token authentication failed",
        headers: HEADERS = None,
    ):
        super().__init__(session, status_code, detail, headers)


class RegistrationRequired(AuthenticationException):
    def __init__(
        self,
        session: UUID,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        detail="Public key registration required",
        headers: HEADERS = None,
    ):
        super().__init__(session, status_code, detail, headers)


class RegistrationFailed(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail="Registration failed",
        headers: HEADERS = None,
    ):
        super().__init__(status_code, detail, headers)


class AlreadyExists(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail="Already exists",
        headers: HEADERS = None,
    ):
        super().__init__(status_code, detail, headers)


class NotExists(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail="Not exists",
        headers: HEADERS = None,
    ):
        super().__init__(status_code, detail, headers)


class NotEnoughSpace(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail="Not enough space",
        headers: HEADERS = None,
    ):
        super().__init__(status_code, detail, headers)
