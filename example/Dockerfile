FROM node:18.7.0-slim AS frontend-build

WORKDIR /srv
ADD frontend/ /srv/

RUN yarn && yarn build

FROM python:3.8

ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app

RUN pip install poetry==1.1.13

COPY . /app
COPY --from=frontend-build /srv/build /app/datapipe_app/frontend

RUN poetry config virtualenvs.create false && poetry install

CMD cd example && uvicorn app:app --host=0.0.0.0 --port=$PORT