# datapipe-app

`datapipe-app` implements two aspects to make every [datapipe](https://github.com/epoch8/datapipe) pipeline to work as
an application:

1. REST API + debug UI based of FastAPI
1. `datapipe` CLI tool

## Common usage

Common pattern to use `datapipe-app` is to create `app.py` with the following code:

```
from datapipe_app import DatapipeApp

from pipeline import ds, catalog, pipeline

app = DatapipeApp(ds, catalog, pipeline)
```

Where `pipeline` is a module that defines common elements: `ds`, `catalog` and
`pipeline`.

## REST API + UI

`DatapipeApp` inherits from `FastApi` app and can be started with server like
`uvicorn`.

```
uvicorn app:app
```

### UI

![Datapipe App UI](docs/datapipe-example-app.png)

### REST API

API documentation can be found at `/api/v1alpha1/docs` sub URL.

## CLI

`datapipe` CLI tool implements useful operations.

### run

`datapipe run --pipeline app`

Does full run of a specific pipeline.

### table list

`datapipe table list`

Lists all tables in pipeline.

### table reset-metadata

`datapipe table reset-metadata TABLE`

Resets metadata for a specific table: sets `updated_ts`, `processed_ts`, `hash`
to `0`.
