from typing import Any, Dict, List, Literal, Optional, Tuple

import pandas as pd
from datapipe.compute import (
    Catalog,
    ComputeStep,
    DataStore,
    Pipeline,
    run_steps,
    run_steps_changelist,
)
from datapipe.step.batch_transform import BaseBatchTransformStep
from datapipe.types import ChangeList, IndexDF, Labels
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Response
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from sqlalchemy.sql.expression import and_, asc, desc, or_, select, text
from sqlalchemy.sql.functions import count

from datapipe_app import models
from datapipe_app.settings import API_SETTINGS


def filter_steps_by_labels(steps: List[ComputeStep], labels: Labels = [], name_prefix: str = "") -> List[ComputeStep]:
    res = []
    for step in steps:
        for k, v in labels:
            if (k, v) not in step.labels:
                break
        else:
            if step.name.startswith(name_prefix):
                res.append(step)

    return res


def update_data(
    ds: DataStore,
    catalog: Catalog,
    steps: List[ComputeStep],
    background_tasks: BackgroundTasks,
    table_name: str,
    upsert: Optional[List[Dict]],
    background: bool,
    enable_changelist: bool = True,
) -> models.UpdateDataResponse:
    dt = catalog.get_datatable(ds, table_name)

    cl = ChangeList()

    if upsert is not None and len(upsert) > 0:
        idx = dt.store_chunk(pd.DataFrame.from_records(upsert))

        cl.append(dt.name, idx)

    # if req.delete is not None and len(req.delete) > 0:
    #     idx = dt.delete_by_idx(
    #         pd.DataFrame.from_records(req.delete)
    #     )

    #     cl.append(dt.name, idx)
    if enable_changelist:
        if background:
            background_tasks.add_task(run_steps_changelist, ds=ds, steps=steps, changelist=cl)
        else:
            run_steps_changelist(ds=ds, steps=steps, changelist=cl)

    return models.UpdateDataResponse(result="ok")


def get_data_get_pd(
    ds: DataStore,
    catalog: Catalog,
    table: str,
    page: int,
    page_size: int,
    filters: Optional[IndexDF],
    order_by: Optional[List[str]],
    order: Literal["asc", "desc"],
) -> Tuple[int, pd.DataFrame, pd.DataFrame]:
    dt = catalog.get_datatable(ds, table)

    meta_schema = dt.meta_table.sql_schema
    meta_tbl = dt.meta_table.sql_table

    sql: Any = select(*meta_schema)
    sql = sql.where(meta_tbl.c.delete_ts.is_(None))
    if filters is not None:
        sql = sql.where(
            and_(
                *[meta_tbl.c[column].in_(filters[column]) for column in filters.columns],
                meta_tbl.c["delete_ts"].is_(None),
            )
        )
    else:
        sql = sql.where(meta_tbl.c["delete_ts"].is_(None))
    sql_count = select(count()).select_from(sql)
    with ds.meta_dbconn.con.begin() as conn:
        total_count = conn.execute(sql_count).scalar()
    assert total_count is not None
    if page * page_size > total_count:
        meta_df = pd.DataFrame(columns=[x.name for x in meta_schema])
        data_df = dt.get_data(IndexDF(meta_df))
    else:
        if order_by is not None:
            if order == "asc":
                sql = sql.order_by(
                    asc(*[meta_tbl.c[column] for column in order_by]),
                )
            elif order == "desc":
                sql = sql.order_by(
                    desc(*[meta_tbl.c[column] for column in order_by]),
                )
        sql = sql.offset(page * page_size).limit(page_size)
        meta_df = pd.read_sql_query(
            sql,
            con=ds.meta_dbconn.con,
        )

        if not meta_df.empty:
            data_df = dt.get_data(IndexDF(meta_df))
            data_df = meta_df.merge(data_df)[data_df.columns]  # save order
        else:
            data_df = pd.DataFrame(columns=[x.name for x in meta_schema])

    return total_count, meta_df, data_df


def get_data_get(
    ds: DataStore,
    catalog: Catalog,
    table: str,
    page: int = 0,
    page_size: int = 20,
    filters: Optional[IndexDF] = None,
    order_by: Optional[List[str]] = None,
    order: Optional[Literal["asc", "desc"]] = None,
) -> models.GetDataResponse:
    if order is None:
        order = "asc"

    total_count, meta_df, data_df = get_data_get_pd(
        ds=ds,
        catalog=catalog,
        table=table,
        page=page,
        page_size=page_size,
        filters=filters,
        order_by=order_by,
        order=order,
    )
    return models.GetDataResponse(
        page=page,
        page_size=page_size,
        total=total_count,
        data=data_df.fillna("").to_dict(orient="records"),
    )


def get_table_data(ds: DataStore, catalog: Catalog, req: models.GetDataRequest) -> models.GetDataResponse:
    dt = catalog.get_datatable(ds, req.table)
    meta_table = dt.meta_table

    sql = (
        select(*meta_table.primary_schema)
        .select_from(meta_table.sql_table)
        .where(meta_table.sql_table.c.delete_ts.is_(None))
    )
    sql.offset(req.page * req.page_size).limit(req.page_size)

    if req.focus is not None:
        filtered_focus_idx = [{k: v for k, v in row.items() if k in dt.primary_keys} for row in req.focus.items_idx]
        primary_key_selectors = [
            and_(*[meta_table.sql_table.c[k] == v for k, v in row.items()]) for row in filtered_focus_idx
        ]
        sql = sql.where(or_(*primary_key_selectors))

    meta_df = pd.read_sql_query(sql, con=meta_table.dbconn.con)

    data_df = pd.DataFrame()
    if not meta_df.empty:
        data_df = dt.get_data(IndexDF(meta_df))
        for col, val in req.filters.items():
            data_df = data_df[data_df[col].astype(str) == val]
        if req.order_by is not None:
            ascending = req.order == "asc"
            data_df.sort_values(by=req.order_by, ascending=ascending, inplace=True)

    return models.GetDataResponse(
        page=req.page,
        page_size=req.page_size,
        total=dt.get_size(),
        data=data_df.fillna("-").to_dict(orient="records"),
    )


def get_transform_data(step: BaseBatchTransformStep, req: models.GetDataRequest) -> models.GetDataResponse:
    sql_table = step.meta_table.sql_table
    sql_schema = step.meta_table.sql_schema

    sql = select(*sql_schema).select_from(sql_table)
    sql = sql.offset(req.page * req.page_size).limit(req.page_size)

    if req.order_by:
        sql = sql.where(text(f"{req.order_by} is not null"))
        sql = sql.order_by(text(f"{req.order_by} {req.order}"))

    if req.focus is not None:
        filtered_focus_idx = [
            {k: v for k, v in row.items() if k in step.meta_table.primary_keys} for row in req.focus.items_idx
        ]
        primary_key_selectors = [and_(*[sql_table.c[k] == v for k, v in row.items()]) for row in filtered_focus_idx]
        sql = sql.where(or_(*primary_key_selectors))

    for col, val in req.filters.items():
        sql = sql.where(sql_table.c[col] == val)

    transform_data = pd.read_sql_query(sql, con=step.meta_table.dbconn.con)

    transform_data = transform_data.drop("priority", axis=1)
    transform_data["process_ts"] = pd.to_datetime(transform_data["process_ts"], unit="s", utc=True)

    with step.meta_table.dbconn.con.begin() as conn:
        sql_count = select(count()).select_from(sql_table)
        for col, val in req.filters.items():
            sql_count = sql_count.where(sql_table.c[col] == val)
        total = conn.execute(sql_count).scalar()
        assert total is not None

    return models.GetDataResponse(
        page=req.page,
        page_size=req.page_size,
        total=total,
        data=transform_data.fillna("-").to_dict(orient="records"),
    )


def make_app(
    ds: DataStore,
    catalog: Catalog,
    pipeline: Pipeline,
    steps: List[ComputeStep],
) -> FastAPI:
    app = FastAPI()

    @app.get("/graph", response_model=models.GraphResponse)
    def get_graph() -> models.GraphResponse:
        def table_response(table_name):
            tbl = catalog.get_datatable(ds, table_name)

            return models.TableResponse(
                name=tbl.name,
                indexes=tbl.primary_keys,
                size=tbl.get_size(),
                store_class=tbl.table_store.__class__.__name__,
            )

        def pipeline_step_response(step: ComputeStep):
            inputs = [i.name for i in step.input_dts]
            outputs = [i.name for i in step.output_dts]

            if isinstance(step, BaseBatchTransformStep):
                step_status = step.get_status(ds=ds) if API_SETTINGS.show_step_status else None

                return models.PipelineStepResponse(
                    type="transform",
                    transform_type=step.__class__.__name__,
                    name=step.get_name(),
                    indexes=step.transform_keys,
                    inputs=inputs,
                    outputs=outputs,
                    total_idx_count=(step_status.total_idx_count if step_status else None),
                    changed_idx_count=(step_status.changed_idx_count if step_status else None),
                )

            else:
                return models.PipelineStepResponse(
                    type="transform",
                    transform_type=step.__class__.__name__,
                    name=step.get_name(),
                    inputs=inputs,
                    outputs=outputs,
                )

        return models.GraphResponse(
            catalog={table_name: table_response(table_name) for table_name in catalog.catalog.keys()},
            pipeline=[pipeline_step_response(step) for step in steps],
        )

    @app.post("/update-data", response_model=models.UpdateDataResponse)
    def update_data_api(
        req: models.UpdateDataRequest,
        background_tasks: BackgroundTasks,
    ) -> models.UpdateDataResponse:
        return update_data(
            ds=ds,
            catalog=catalog,
            steps=filter_steps_by_labels(steps, labels=req.labels),
            background_tasks=background_tasks,
            table_name=req.table_name,
            upsert=req.upsert,
            background=req.background,
            enable_changelist=req.enable_changelist,
        )

    # /table/<table_name>?page=1&id=111&another_filter=value&sort=<+|->column_name
    @app.get("/get-data", response_model=models.GetDataResponse)
    def get_data_get_api(
        table: str,
        page: int = 0,
        page_size: int = 20,
    ) -> models.GetDataResponse:
        return get_data_get(ds, catalog, table, page, page_size)

    @app.post("/get-table-data", response_model=models.GetDataResponse)
    def get_data_post_api(req: models.GetDataRequest) -> models.GetDataResponse:
        return get_table_data(ds, catalog, req)

    @app.post("/get-transform-data")
    def get_meta_data_api(req: models.GetDataRequest) -> models.GetDataResponse:
        filtered_steps = filter_steps_by_labels(steps, name_prefix=req.table)
        if len(filtered_steps) != 1:
            raise HTTPException(status_code=404, detail="Step not found")
        step = filtered_steps[0]

        # maybe infer on type or smth?
        if not isinstance(step, BaseBatchTransformStep):
            return models.GetDataResponse(
                page=req.page,
                page_size=req.page_size,
                total=0,
                data=[],
            )

        return get_transform_data(step, req)

    @app.post("/get-data-by-idx")
    def get_data_by_idx(req: models.GetDataByIdxRequest):
        dt = catalog.get_datatable(ds, req.table_name)

        res = dt.get_data(idx=IndexDF(pd.DataFrame.from_records(req.idx)))

        return res.to_dict(orient="records")

    @app.post("/run")
    def run():
        run_steps(ds=ds, steps=steps)

    # TODO refactor out to component based extension system
    # TODO automatic setup of webhook on project creation
    @app.post("/labelstudio-webhook")
    def labelstudio_webhook(
        request: Dict,
        background_tasks: BackgroundTasks,
        table_name: str = Query(..., title="Input table name"),
        data_field: List = Query(..., title="Fields to get from data"),
        background: bool = Query(False, title="Run as Background Task (default = False)"),
    ) -> models.UpdateDataResponse:
        upsert = [
            {
                **{k: v for k, v in request["task"]["data"].items() if k in data_field},
                "annotations": [request["annotation"]],
            }
        ]

        return update_data(
            ds=ds,
            catalog=catalog,
            steps=steps,
            background_tasks=background_tasks,
            table_name=table_name,
            upsert=upsert,
            background=background,
        )

    @app.get("/get-file")
    def get_file(filepath: str):
        import mimetypes

        import fsspec

        with fsspec.open(filepath) as f:
            mime = mimetypes.guess_type(filepath)
            assert mime[0] is not None
            return Response(content=f.read(), media_type=mime[0])  # type: ignore

    FastAPIInstrumentor.instrument_app(app, excluded_urls="docs")

    return app
