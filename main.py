from fastapi import FastAPI

import crud
from database import Base, engine

Base.metadata.create_all(engine)

app = FastAPI()
