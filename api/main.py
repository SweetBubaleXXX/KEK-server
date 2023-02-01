import uvicorn

from .app import app
from .db.engine import Base, engine

Base.metadata.create_all(engine)


def main():
    uvicorn.run(app)
