import os
from sqlalchemy import JSON, Column, Integer, String, Boolean

import pandas as pd

from datapipe.core_steps import BatchTransform
from datapipe.compute import DataStore, Catalog, Table, Pipeline, build_compute
from datapipe.store.database import TableStoreDB, DBConn

DB_CONN_URI = os.environ.get("DB_CONN_URI", "sqlite:///store.sqlite")

# dbconn = DBConn("sqlite:///store.sqlite")
# dbconn = DBConn("sqlite:///:memory:")
# dbconn = DBConn("postgresql://postgres:postgres@localhost:5432/postgres")
dbconn = DBConn(DB_CONN_URI)

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
        "events2": Table(
            store=TableStoreDB(
                name="events2",
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
                    Column("offer_clicks", JSON()),
                    Column("events_count", Integer()),
                    Column("active", Boolean()),
                ],
                create_table=False,
            )
        ),
        "user_profile2": Table(
            store=TableStoreDB(
                name="user_profile2",
                dbconn=dbconn,
                data_sql_schema=[
                    Column("user_id", Integer(), primary_key=True),
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
                    Column("lang", String(length=100)),
                ],
                create_table=False,
            )
        ),
        "user_lang2": Table(
            store=TableStoreDB(
                name="user_lang2",
                dbconn=dbconn,
                data_sql_schema=[
                    Column("user_id", Integer(), primary_key=True),
                    Column("lang", String(length=100)),
                ],
                create_table=False,
            )
        ),
    }
)


def agg_profile(df: pd.DataFrame) -> pd.DataFrame:
    res = []

    res_lang = []

    for user_id, grp in df.groupby("user_id"):
        res.append(
            {
                "user_id": user_id,
                "offer_clicks": [
                    x["offer_id"] for x in grp["event"] if x["event_type"] == "click"
                ],
                "events_count": len(grp),
                "active": True,
            }
        )

        res_lang.append(
            {
                "user_id": user_id,
                "lang": grp.iloc[-1]["event"]["lang"],
            }
        )

    return (
        pd.DataFrame.from_records(res),
        pd.DataFrame.from_records(res_lang),
    )


pipeline = Pipeline(
    steps=[
        BatchTransform(
            agg_profile,
            inputs=["events"],
            outputs=["user_profile", "user_lang"],
        ),
        BatchTransform(
            agg_profile,
            inputs=["events2"],
            outputs=["user_profile2", "user_lang2"]
        )
    ]
)

ds = DataStore(dbconn, create_meta_table=False)

# steps = build_compute(ds, catalog, pipeline)