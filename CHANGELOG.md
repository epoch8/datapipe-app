# 0.1.11

* Add `GET /api/v1alpha1/get-file` to get `gs://` or `s3://` files from frontend

# 0.1.10

* Add `POST /api/v1alpha1/get-data` with support for filtering

# 0.1.9

* Use `DataTable.get_size()`, fixes
  [#14](https://github.com/epoch8/datapipe-app/issues/14)

# 0.1.7, 0.1.8

* Relax FastAPI requirements for compatibility with Fiftyone

# 0.1.6

* Fix [#13](https://github.com/epoch8/datapipe-app/issues/13) - boolean values
  visualization.

# 0.1.5

* Fix [#12](https://github.com/epoch8/datapipe-app/issues/12) - transform nodes
  with the same name are incorrectly merged into one.

# 0.1.4

* Relax `uvicorn` requirements (>= 0.17)

# 0.1.3

* Relax `fastapi` requirements (>= 0.75)

# 0.1.2

* New CLI commands: `table list`, `table reset-metadata`

# 0.1.1

* Fixes [#2](https://github.com/epoch8/datapipe-app/issues/2),
  [#7](https://github.com/epoch8/datapipe-app/issues/7) - data table
  visualization issues

# 0.1.0

* Initial `datapipe-app` release
