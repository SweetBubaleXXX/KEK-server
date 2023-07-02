import uvicorn

from .app import app


def main():
    uvicorn.run(app)
