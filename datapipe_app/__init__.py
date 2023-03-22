import sys
import os.path
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from datapipe.datatable import DataStore
from datapipe.compute import Catalog, Pipeline, DatapipeApp

import datapipe_app.api_v1alpha1 as api_v1alpha1


class DatapipeAPI(FastAPI, DatapipeApp):
    def __init__(self, ds: DataStore, catalog: Catalog, pipeline: Pipeline):
        DatapipeApp.__init__(self, ds, catalog, pipeline)
        FastAPI.__init__(self)

        self.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.api = FastAPI()

        self.api.mount("/v1alpha1", api_v1alpha1.DatpipeAPIv1(ds, catalog, pipeline, self.steps), name="v1alpha1")

        self.mount("/api", self.api, name="api")
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
