from pipeline import ds, catalog, pipeline, dbconn
from datapipe_app import DatapipeApp

app = DatapipeApp(ds, catalog, pipeline)
