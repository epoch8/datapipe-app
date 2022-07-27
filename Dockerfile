FROM python:3.8

ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app

RUN pip install poetry==1.1.13
COPY poetry.lock pyproject.toml /app/

RUN poetry config virtualenvs.create false && poetry install --no-dev

COPY . /app

# For tests use 'export $(cat .env | xargs)'

CMD exec uvicorn api:app --host=0.0.0.0 --port=$PORT
