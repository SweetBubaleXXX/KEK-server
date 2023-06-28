FROM python:3.11-alpine

WORKDIR /app

COPY ./requirements.txt /app/

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./api /app/api

EXPOSE 80

CMD ["uvicorn", "api.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
