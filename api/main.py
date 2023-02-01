import uvicorn

from .app import app
from .db import engine as db

db.Base.metadata.create_all(db.engine)


def main():
    uvicorn.run(app)
