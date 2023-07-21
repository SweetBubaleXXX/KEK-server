FROM python:3.11-alpine

ARG DB_DRIVER=aiosqlite

WORKDIR /app

COPY ./requirements.txt ./

COPY ./requirements-${DB_DRIVER}.txt ./

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt 

RUN pip install --no-cache-dir --upgrade -r ./requirements-${DB_DRIVER}.txt

COPY ./api ./api

COPY ./migrations ./migrations

COPY ./alembic.ini ./

EXPOSE 80

CMD ["uvicorn", "api.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
