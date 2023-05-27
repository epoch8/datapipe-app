from pipeline import catalog, ds, pipeline

from datapipe_app import DatapipeAPI

app = DatapipeAPI(ds, catalog, pipeline)
