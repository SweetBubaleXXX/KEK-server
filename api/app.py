from fastapi import FastAPI

from .exceptions import client, handlers
from .routers import files, folders, registration

app = FastAPI()

app.add_exception_handler(client.RegistrationRequired,
                          handlers.registration_required_handler)
app.add_exception_handler(client.AuthenticationRequired,
                          handlers.authentication_required_handler)

app.include_router(registration.router)
app.include_router(folders.router, prefix="/folders")
app.include_router(files.router, prefix="/files")
