import os
import datetime

import click

CONF = os.path.join(os.path.expanduser('~'), '.watson')


@click.group()
def cli():
    pass


@cli.command()
@click.argument('project')
def start(project):
    start_time = datetime.datetime.now()
    click.echo("Starting {} at {:%H:%M:%S}".format(project, start_time))

if __name__ == '__main__':
    cli()
