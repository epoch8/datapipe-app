import os.path
import sys

import click
from opentelemetry import trace  # type: ignore
from opentelemetry.sdk.trace import TracerProvider  # type: ignore
from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
from opentelemetry.sdk.trace.export import ConsoleSpanExporter  # type: ignore
from termcolor import colored

from datapipe_app import DatapipeApp


def load_pipeline(pipeline_name: str) -> DatapipeApp:
    pipeline_split = pipeline_name.split(":")

    if len(pipeline_split) == 1:
        module_name = pipeline_split[0]
        app_name = "app"
    elif len(pipeline_split) == 2:
        module_name, app_name = pipeline_split
    else:
        raise Exception(
            f"Expected PIPELINE in format 'module:app' got '{pipeline_name}'"
        )

    from importlib import import_module

    sys.path.append(os.getcwd())

    pipeline_mod = import_module(module_name)
    app = getattr(pipeline_mod, app_name)

    assert isinstance(app, DatapipeApp)

    return app


@click.group()
@click.option("--debug", is_flag=True, help="Log debug output")
@click.option("--debug-sql", is_flag=True, help="Log SQL queries VERY VERBOSE")
@click.option("--trace-stdout", is_flag=True, help="Log traces to console")
@click.option("--trace-jaeger", is_flag=True, help="Enable tracing to Jaeger")
@click.option(
    "--trace-jaeger-host", type=click.STRING, default="localhost", help="Jaeger host"
)
@click.option("--trace-jaeger-port", type=click.INT, default=14268, help="Jaeger port")
def cli(
    debug: bool,
    debug_sql: bool,
    trace_stdout: bool,
    trace_jaeger: bool,
    trace_jaeger_host: str,
    trace_jaeger_port: int,
) -> None:
    import logging

    if debug:
        datapipe_logger = logging.getLogger("datapipe")
        datapipe_logger.setLevel(logging.DEBUG)

        datapipe_core_steps_logger = logging.getLogger("datapipe.core_steps")
        datapipe_core_steps_logger.setLevel(logging.DEBUG)

        logging.basicConfig(level=logging.DEBUG)

        datapipe_core_steps_logger.debug("Test debug")
    else:
        logging.basicConfig(level=logging.INFO)

    if debug_sql:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    if trace_stdout:
        provider = TracerProvider()
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

    if trace_jaeger:
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter  # type: ignore
        from opentelemetry.sdk.resources import SERVICE_NAME  # type: ignore
        from opentelemetry.sdk.resources import Resource  # type: ignore

        trace.set_tracer_provider(
            TracerProvider(resource=Resource.create({SERVICE_NAME: "datapipe"}))
        )

        # create a JaegerExporter
        jaeger_exporter = JaegerExporter(
            # configure agent
            # agent_host_name='localhost',
            # agent_port=6831,
            # optional: configure also collector
            collector_endpoint=f"http://{trace_jaeger_host}:{trace_jaeger_port}/api/traces?format=jaeger.thrift",
            # username=xxxx, # optional
            # password=xxxx, # optional
            # max_tag_value_length=None # optional
        )

        # Create a BatchSpanProcessor and add the exporter to it
        span_processor = BatchSpanProcessor(jaeger_exporter)

        # add to the tracer
        trace.get_tracer_provider().add_span_processor(span_processor)  # type: ignore


@cli.group()
def table():
    pass


@table.command()
@click.option("--pipeline", type=click.STRING, default="app")
def list(pipeline: str) -> None:
    app = load_pipeline(pipeline)

    for table in sorted(app.catalog.catalog.keys()):
        print(table)


@table.command()
@click.option("--pipeline", type=click.STRING, default="app")
@click.argument("table")
def reset_metadata(pipeline: str, table: str) -> None:
    app = load_pipeline(pipeline)

    dt = app.catalog.get_datatable(app.ds, table)

    app.ds.meta_dbconn.con.execute(
        dt.meta_table.sql_table.update().values(process_ts=0, update_ts=0)
    )


@cli.command()
@click.option("--pipeline", type=click.STRING, default="app")
def run(pipeline: str) -> None:
    from datapipe.compute import run_steps

    app = load_pipeline(pipeline)

    run_steps(app.ds, app.steps)


@cli.group()
def db():
    pass


@db.command()
@click.option("--pipeline", type=click.STRING, default="app")
def create_all(pipeline: str) -> None:
    app = load_pipeline(pipeline)

    app.ds.meta_dbconn.sqla_metadata.create_all(app.ds.meta_dbconn.con)


@cli.command()
@click.option("--pipeline", type=click.STRING, default="app")
@click.option("--tables", type=click.STRING, default="*")
@click.option("--fix", is_flag=True, type=click.BOOL, default=False)
def lint(pipeline: str, tables: str, fix: bool) -> None:
    app = load_pipeline(pipeline)

    from . import lints

    checks = [lints.LintDeleteTSIsNewerThanUpdateOrProcess()]

    tables_from_catalog = app.catalog.catalog.keys()
    print(f"Pipeline '{pipeline}' contains {len(tables_from_catalog)} tables")

    if tables == "*":
        tables_to_process = tables_from_catalog
    else:
        tables_to_process = tables.split(",")

    for table_name in sorted(tables_to_process):
        print(f"Checking '{table_name}': ", end="")

        dt = app.catalog.get_datatable(app.ds, table_name)

        errors = []

        for check in checks:
            (status, msg) = check.check(dt)

            if status == lints.LintStatus.OK:
                print(".", end="")
            elif status == lints.LintStatus.SKIP:
                print("S", end="")
            elif status == lints.LintStatus.FAIL:
                print(colored("F", "red"), end="")
                errors.append((check, msg))

        if len(errors) == 0:
            print(colored(" ok", "green"))
        else:
            print(colored(" FAIL", "red"))
            for check, msg in errors:
                print(f" * {check.desc}: {msg}", end="")

                if fix:
                    try:
                        check.fix(dt)
                        print("... " + colored("FIXED", "green"), end="")
                    except:
                        print("... " + colored("FAILED TO FIX", "red"), end="")
                
                print()
            print()


@cli.group()
def step():
    pass


@step.command()  # type: ignore
@click.option("--pipeline", type=click.STRING, default="app")
def list(pipeline: str) -> None:
    app = load_pipeline(pipeline)

    for step in app.steps:
        print(step.name)


@step.command()  # type:ignore
@click.option("--pipeline", type=click.STRING, default="app")
@click.argument("step")
def run(pipeline: str, step: str) -> None:
    app = load_pipeline(pipeline)

    steps_to_run = [i for i in app.steps if i.name.startswith(step)]

    if len(steps_to_run) > 0:
        for step_obj in steps_to_run:
            step_obj.run_full(app.ds)
    else:
        print(f"There's no step with name '{step}'")
