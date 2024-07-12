import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Set

import pandas as pd
from datapipe.compute import Catalog, ComputeStep, DataStore, Pipeline, run_steps
from datapipe.step.batch_transform import BaseBatchTransformStep
from datapipe.store.database import TableStoreDB
from datapipe.types import Labels
from fastapi import (
    BackgroundTasks,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from sqlalchemy.sql.expression import and_, or_, select, text
from sqlalchemy.sql.functions import count, func

from datapipe_app import models
from datapipe_app.settings import API_SETTINGS


def get_table_store_db_data(table_store: TableStoreDB, req: models.GetDataRequest) -> models.GetDataResponse:
    sql_schema = table_store.data_sql_schema
    sql_table = table_store.data_table

    sql = select(*sql_schema).select_from(sql_table)
    if req.focus is not None:
        filtered_focus_idx = [
            {k: v for k, v in row.items() if k in table_store.primary_keys} for row in req.focus.items_idx
        ]
        primary_key_selectors = [and_(*[sql_table.c[k] == v for k, v in row.items()]) for row in filtered_focus_idx]
        sql = sql.where(or_(*primary_key_selectors))

    for col, val in req.filters.items():
        sql = sql.where(sql_table.c[col] == val)

    sql_count = select(count()).select_from(sql.subquery())

    if req.order_by:
        sql = sql.where(text(f"{req.order_by} is not null"))
        sql = sql.order_by(text(f"{req.order_by} {req.order}"))

    sql.offset(req.page * req.page_size).limit(req.page_size)

    data_df = pd.read_sql_query(sql, con=table_store.dbconn.con)

    with table_store.dbconn.con.begin() as conn:
        total = conn.execute(sql_count).scalar_one_or_none()
        assert total is not None

    return models.GetDataResponse(
        page=req.page,
        page_size=req.page_size,
        total=total,
        data=data_df.fillna("-").to_dict(orient="records"),
    )


def get_table_data(ds: DataStore, catalog: Catalog, req: models.GetDataRequest) -> models.GetDataResponse:
    dt = catalog.get_datatable(ds, req.table)
    table_store = dt.table_store

    if isinstance(table_store, TableStoreDB):
        return get_table_store_db_data(table_store, req)

    raise HTTPException(status_code=500, detail="Not implemented")


def get_transform_data(step: BaseBatchTransformStep, req: models.GetDataRequest) -> models.GetDataResponse:
    sql_table = step.meta_table.sql_table
    sql_schema = step.meta_table.sql_schema

    sql = select(*sql_schema).select_from(sql_table)

    if req.focus is not None:
        filtered_focus_idx = [
            {k: v for k, v in row.items() if k in step.meta_table.primary_keys} for row in req.focus.items_idx
        ]
        primary_key_selectors = [and_(*[sql_table.c[k] == v for k, v in row.items()]) for row in filtered_focus_idx]
        sql = sql.where(or_(*primary_key_selectors))

    for col, val in req.filters.items():
        if col == "process_ts":
            val = datetime.fromisoformat(val).timestamp()
            # Postgres 7 digits precision, datetime.timestamp() has 6 digits so we need to add some tolerance
            sql = sql.where(func.abs(sql_table.c[col] - val) < 0.000001)
        else:
            sql = sql.where(sql_table.c[col] == val)

    sql_count = select(count()).select_from(sql.subquery())

    if req.order_by:
        sql = sql.where(text(f"{req.order_by} is not null"))
        sql = sql.order_by(text(f"{req.order_by} {req.order}"))

    sql = sql.offset(req.page * req.page_size).limit(req.page_size)

    transform_data = pd.read_sql_query(sql, con=step.meta_table.dbconn.con)

    transform_data = transform_data.drop("priority", axis=1)
    transform_data["process_ts"] = pd.to_datetime(transform_data["process_ts"], unit="s", utc=True)

    with step.meta_table.dbconn.con.begin() as conn:
        total = conn.execute(sql_count).scalar_one_or_none()
        assert total is not None

    return models.GetDataResponse(
        page=req.page,
        page_size=req.page_size,
        total=total,
        data=transform_data.fillna("-").to_dict(orient="records"),
    )


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


class RunningStepsHelper:
    def __init__(self, ds: DataStore) -> None:
        self._ds = ds
        self._running_steps: Dict[str, Dict[str, Any]] = {}
        self._transform_web_sockets: Dict[str, Set[WebSocket]] = {}
        self._thread_pool = ThreadPoolExecutor(max_workers=4)

    async def add_ws(self, websocket: WebSocket, transform: str) -> None:
        if transform not in self._transform_web_sockets:
            self._transform_web_sockets[transform] = set()
        self._transform_web_sockets[transform].add(websocket)

    async def remove_ws(self, websocket: WebSocket, transform: str) -> None:
        if transform not in self._transform_web_sockets:
            return
        self._transform_web_sockets[transform].remove(websocket)

    def transform_is_running(self, transform: str) -> bool:
        if transform not in self._running_steps:
            return False
        return self._running_steps[transform]["running"]

    def get_data_for_transform(self, transform: str) -> Dict[str, Any]:
        transform_data = self._running_steps[transform]
        return {
            "status": "running" if transform_data["running"] else "finished",
            "processed": transform_data["processed"],
            "total": transform_data["start_changed_idx_count"],
        }

    def add_transform(self, transform: str, step: ComputeStep) -> None:
        step_status = step.get_status(ds=self._ds)
        self._running_steps[transform] = {
            "running": True,
            "step": step,
            "start_total_idx_count": step_status.total_idx_count,
            "start_changed_idx_count": step_status.changed_idx_count,
            "processed": 0,
        }
        self._thread_pool.submit(self._run_step, transform)

    def _run_step(self, transform: str) -> None:
        step = self._running_steps[transform]["step"]
        run_steps(ds=self._ds, steps=[step])
        self._running_steps[transform]["running"] = False

    def _update_transform_status(self, transform: str) -> None:
        transform_data = self._running_steps[transform]
        step = transform_data["step"]
        step_status = step.get_status(ds=self._ds)
        total_diff = step_status.total_idx_count - transform_data["start_total_idx_count"]
        new_processed = transform_data["start_changed_idx_count"] - (step_status.changed_idx_count - total_diff)
        transform_data["processed"] = new_processed

    async def update_transform_status(self, transform: str) -> None:
        while self.transform_is_running(transform):
            self._update_transform_status(transform)
            await asyncio.sleep(1)

        self._update_transform_status(transform=transform)
        for ws in self._transform_web_sockets[transform]:
            try:
                await ws.send_json(self.get_data_for_transform(transform))
            except RuntimeError:
                pass


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

    _running_steps_helper = RunningStepsHelper(ds)

    @app.websocket("/ws/transform/{transform}/run-status")
    async def ws_transform_run_status(websocket: WebSocket, transform: str):
        await websocket.accept()
        await _running_steps_helper.add_ws(websocket, transform)
        try:
            while True:
                if _running_steps_helper.transform_is_running(transform):
                    data = _running_steps_helper.get_data_for_transform(transform)
                    await websocket.send_json(data)
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            await _running_steps_helper.remove_ws(websocket, transform)

    @app.post("/transform/run", response_model=models.RunStepResponse)
    def run_transform(request: models.RunStepRequest, background_tasks: BackgroundTasks):
        # TODO: Some lock here??? to prevent multiple runs at the same time
        if _running_steps_helper.transform_is_running(request.transform):
            return models.RunStepResponse(status="already running")

        filtered_steps = filter_steps_by_labels(steps, name_prefix=request.transform)
        if len(filtered_steps) != 1:
            raise HTTPException(status_code=404, detail="Step not found")
        step = filtered_steps[0]
        if not isinstance(step, BaseBatchTransformStep):
            raise HTTPException(status_code=400, detail="Step is not allowed to run")

        step_status = step.get_status(ds=ds)
        if step_status.changed_idx_count == 0:
            return models.RunStepResponse(status="no changes")

        _running_steps_helper.add_transform(transform=request.transform, step=step)
        background_tasks.add_task(_running_steps_helper.update_transform_status, transform=request.transform)

        return models.RunStepResponse(status="ok")

    FastAPIInstrumentor.instrument_app(app, excluded_urls="docs")

    return app
