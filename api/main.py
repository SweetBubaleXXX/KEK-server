import uvicorn
from fastapi import Body, Depends, FastAPI
from KEK.hybrid import PublicKEK

from . import crud
from .config import settings
from .database import Base, engine
from .dependencies import get_db, get_key, verify_token
from .exceptions import exceptions, handlers
from .models import KeyRecord
from .schemas import SignedRequest

Base.metadata.create_all(engine)

app = FastAPI()

app.add_exception_handler(exceptions.RegistrationRequired,
                          handlers.registration_required_handler)
app.add_exception_handler(exceptions.AuthenticationRequired,
                          handlers.authentication_required_handler)


@app.post("/", dependencies=[Depends(verify_token)])
def index(request: SignedRequest, key: PublicKEK = Depends(get_key)):
    ...


if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port)
