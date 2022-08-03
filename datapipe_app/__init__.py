import sys
import os.path
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from datapipe.datatable import DataStore
from datapipe.compute import build_compute, Catalog, Pipeline

import datapipe_app.api_v1alpha1 as api_v1alpha1


class DatapipeApp(FastAPI):
    def __init__(self, ds: DataStore, catalog: Catalog, pipeline: Pipeline):
        FastAPI.__init__(self)

        self.ds = ds
        self.catalog = catalog
        self.pipeline = pipeline

        self.steps = build_compute(ds, catalog, pipeline)

        self.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        api_v1_app = api_v1alpha1.DatpipeAPIv1(ds, catalog, pipeline, self.steps)

        self.mount("/api/v1alpha1", api_v1_app, name="api_v1")
        self.mount(
            "/",
            StaticFiles(
                directory=os.path.join(os.path.dirname(__file__), "frontend/"),
                html=True,
            ),
            name="static",
        )


def setup_logging(level=logging.INFO):
    root_logger = logging.getLogger("datapipe")
    root_logger.setLevel(level)

    handler = logging.StreamHandler(stream=sys.stdout)
    root_logger.addHandler(handler)
