from typing import Any, Dict, Optional

from fastapi import status
from fastapi.exceptions import HTTPException


class RegistrationRequired(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        detail: Any = "Public key registration required",
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code, detail, headers)


class AuthenticationRequired(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        detail: Any = "Token authentication required",
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code, detail, headers)


class AuthenticationFailed(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: Any = "Token authentication failed",
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code, detail, headers)
