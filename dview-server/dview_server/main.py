import click
from dview_server.api import APP


@click.group()
def cli():
    pass


@cli.command()
@click.option("--host", default='localhost',
              help="server host", envvar="HOST")
@click.option("--port", default=5010, type=int,
              help="server port", envvar="PORT")
@click.option("-c", "--config", "config_file",
              required=True, help="config file")
def serve(host, port,config_file):
    print("Config file: ",config_file)
    APP.run(host=host, port=port, debug=True)
