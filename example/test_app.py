# TODO: remove

import os
import sys
import time
from typing import Tuple

import pandas as pd
import sqlalchemy as sa
from datapipe.compute import Catalog, DataStore, Pipeline, Table, run_steps
from datapipe.step.batch_transform import BatchTransform
from datapipe.store.database import DBConn, TableStoreDB
from sqlalchemy import JSON, Boolean, Column, Integer, String

from datapipe_app import DatapipeAPI

DB_CONN_URI = os.environ.get("DB_CONN_URI", "sqlite+pysqlite3:///store.sqlite")

# dbconn = DBConn("sqlite:///store.sqlite")
# dbconn = DBConn("sqlite:///:memory:")
dbconn = DBConn("postgresql://postgres:postgres@localhost:5432/postgres")
# dbconn = DBConn(DB_CONN_URI)

catalog = Catalog(
    {
        "events": Table(
            store=TableStoreDB(
                name="events",
                dbconn=dbconn,
                data_sql_schema=[
                    Column("user_id", Integer(), primary_key=True),
                    Column("event_id", Integer(), primary_key=True),
                    Column("event", JSON()),
                ],
                create_table=False,
            )
        ),
        "user_profile": Table(
            store=TableStoreDB(
                name="user_profile",
                dbconn=dbconn,
                data_sql_schema=[
                    Column("user_id", Integer(), primary_key=True),
                    Column("event_id", Integer(), primary_key=True),
                    Column("offer_clicks", JSON()),
                    Column("events_count", Integer()),
                    Column("active", Boolean()),
                ],
                create_table=False,
            )
        ),
        "user_lang": Table(
            store=TableStoreDB(
                name="user_lang",
                dbconn=dbconn,
                data_sql_schema=[
                    Column("user_id", Integer(), primary_key=True),
                    Column("event_id", Integer(), primary_key=True),
                    Column("lang", String(length=100)),
                ],
                create_table=False,
            )
        ),
        "events_test": Table(
            store=TableStoreDB(
                name="events_test",
                dbconn=dbconn,
                data_sql_schema=[
                    Column("user_id", Integer(), primary_key=True),
                    Column("event_id", Integer(), primary_key=True),
                    Column("event", JSON()),
                ],
                create_table=False,
            )
        ),
    }
)


def agg_profile(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    res = []

    res_lang = []

    res_lang_test = []

    for user_id, grp in df.groupby("user_id"):
        res.append(
            {
                "user_id": user_id,
                "event_id": grp.iloc[-1]["event_id"],
                "offer_clicks": [x["offer_id"] for x in grp["event"] if x["event_type"] == "click"],
                "events_count": len(grp),
                "active": True,
            }
        )

        res_lang.append(
            {
                "user_id": user_id,
                "event_id": grp.iloc[-1]["event_id"],
                "lang": grp.iloc[-1]["event"]["lang"],
            }
        )

        if os.getenv("SHOULD_SLEEP") == "True":
            time.sleep(1)

    return (
        pd.DataFrame.from_records(res),
        pd.DataFrame.from_records(res_lang),
        df,
    )


pipeline = Pipeline(
    steps=[
        BatchTransform(
            agg_profile,
            inputs=["events"],
            outputs=["user_profile", "user_lang", "events_test"],
            chunk_size=1,
        ),
    ]
)

ds = DataStore(dbconn, create_meta_table=False)

app = DatapipeAPI(ds, catalog, pipeline)


def drop_tables():
    events_table = ds.get_table("events")
    assert isinstance(events_table.table_store, TableStoreDB)
    with events_table.table_store.dbconn.con.begin() as conn:
        conn.execute(sa.text("DROP SCHEMA public CASCADE"))
        conn.execute(sa.text("CREATE SCHEMA public"))


def create_tables():
    app.ds.meta_dbconn.sqla_metadata.create_all(app.ds.meta_dbconn.con)


def add_data(should_run_steps: bool = False, new: bool = False) -> None:
    events_table = ds.get_table("events")
    data = []
    for i in range(10):
        for j in range(10):
            data.append(
                {
                    "user_id": i,
                    "event_id": 10 - j,
                    "event": {"event_type": "click", "offer_id": 1 if not new else 2, "lang": "en"},
                }
            )
    events_table.store_chunk(pd.DataFrame(data))

    if should_run_steps:
        run_steps(ds=ds, steps=app.steps)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == "reset":
                drop_tables()
                create_tables()
            if arg == "add":
                add_data()
            if arg == "add-new":
                add_data(new=True)
            if arg == "run":
                run_steps(ds=ds, steps=app.steps)
    else:
        add_data(should_run_steps=True)
