from fastapi import FastAPI

from .exceptions import exceptions, handlers
from .routers import registration, folders

app = FastAPI()

app.add_exception_handler(exceptions.RegistrationRequired,
                          handlers.registration_required_handler)
app.add_exception_handler(exceptions.AuthenticationRequired,
                          handlers.authentication_required_handler)

app.include_router(registration.router)
app.include_router(folders.router)
