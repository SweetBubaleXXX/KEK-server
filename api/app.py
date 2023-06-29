from fastapi import FastAPI

from .exceptions import client, core, handlers
from .routers import files, folders, keys

app = FastAPI()

app.add_exception_handler(
    client.RegistrationRequired, handlers.registration_required_handler
)
app.add_exception_handler(
    client.AuthenticationRequired, handlers.authentication_required_handler
)
app.add_exception_handler(
    core.NoAvailableStorage, handlers.no_available_storage_handler
)

app.include_router(keys.router)
app.include_router(folders.router, prefix="/folders")
app.include_router(files.router, prefix="/files")
