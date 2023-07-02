from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db.engine import Base, engine
from .exceptions import client, core, handlers
from .routers import files, folders, keys


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

app.add_exception_handler(
    client.RegistrationRequired, handlers.registration_required_handler
)
app.add_exception_handler(
    client.AuthenticationRequired, handlers.authentication_required_handler
)
app.add_exception_handler(
    client.AuthenticationFailed, handlers.authentication_required_handler
)
app.add_exception_handler(
    core.NoAvailableStorage, handlers.no_available_storage_handler
)

app.include_router(keys.router)
app.include_router(folders.router, prefix="/folders")
app.include_router(files.router, prefix="/files")
