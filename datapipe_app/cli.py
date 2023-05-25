import click

from datapipe.compute import DatapipeApp


def register_commands(cli: click.Group):
    @cli.command()
    @click.option("--host", type=click.STRING, default="0.0.0.0")
    @click.option("--port", type=click.INT, default=8000)
    @click.pass_context
    def api(ctx: click.Context, host: str, port: int) -> None:
        app: DatapipeApp = ctx.obj["pipeline"]

        import uvicorn

        uvicorn.run(app, host=host, port=port)
