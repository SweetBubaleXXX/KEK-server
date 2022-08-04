import uvicorn
from fastapi import FastAPI

from . import crud
from .config import settings
from .database import Base, engine

Base.metadata.create_all(engine)

app = FastAPI()

if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port)
