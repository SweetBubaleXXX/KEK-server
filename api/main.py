from fastapi import Depends, FastAPI

from .db import engine as db
from .dependencies import verify_token
from .exceptions import exceptions, handlers
from .routers import registration

db.Base.metadata.create_all(db.engine)

app = FastAPI()

app.add_exception_handler(exceptions.RegistrationRequired,
                          handlers.registration_required_handler)
app.add_exception_handler(exceptions.AuthenticationRequired,
                          handlers.authentication_required_handler)

app.include_router(registration.router)


@app.post("/", dependencies=[Depends(verify_token)])
def index():
    ...
