import click

from datapipe.compute import DatapipeApp


def register_commands(cli: click.Group):
    @cli.command()
    @click.pass_context
    def api(ctx: click.Context) -> None:
        app: DatapipeApp = ctx.obj["pipeline"]

        import uvicorn

        uvicorn.run(app, host="0.0.0.0")
