from typing import Any

from fastapi import status
from fastapi.exceptions import HTTPException

HEADERS = dict[str, Any] | None


class RegistrationRequired(HTTPException):
    def __init__(
        self,
        key_id: str,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        detail="Public key registration required",
        headers: HEADERS = None,
    ):
        self.key_id = key_id
        super().__init__(status_code, detail, headers)


class AuthenticationRequired(HTTPException):
    def __init__(
        self,
        key_id: str,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        detail="Token authentication required",
        headers: HEADERS = None,
    ):
        self.key_id = key_id
        super().__init__(status_code, detail, headers)


class AuthenticationFailed(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail="Token authentication failed",
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
