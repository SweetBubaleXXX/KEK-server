from fastapi import Body, Depends, FastAPI, status
from fastapi.exceptions import HTTPException
from KEK.exceptions import KeyLoadingError
from KEK.hybrid import PublicKEK
from sqlalchemy.orm import Session

from . import crud
from .db import Base, engine
from .dependencies import get_db, get_key, get_session, verify_token
from .exceptions import exceptions, handlers
from .schemas import SignedPublicKeyInfo, SignedRequest

Base.metadata.create_all(engine)

app = FastAPI()

app.add_exception_handler(exceptions.RegistrationRequired,
                          handlers.registration_required_handler)
app.add_exception_handler(exceptions.AuthenticationRequired,
                          handlers.authentication_required_handler)


@app.post("/", dependencies=[Depends(verify_token)])
def index(request: SignedRequest, key: PublicKEK = Depends(get_key)):
    ...


@app.post("/register")
def register_key(request: SignedPublicKeyInfo, db: Session = Depends(get_db)):
    try:
        key = PublicKEK.load(request.public_key.encode("ascii"))
        assert key.key_id.hex() == request.key_id
    except (KeyLoadingError, AssertionError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail="Could not load public key")
    verify_token(request, key, get_session())
    if not crud.get_key(db, request.key_id):
        crud.add_key(db, request.key_id, request.public_key)
