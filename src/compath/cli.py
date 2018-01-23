# -*- coding: utf-8 -*-

from __future__ import print_function

import logging

import click

from bio2bel_kegg.manager import Manager as KeggManager
from bio2bel_reactome.manager import Manager as ReactomeManager
from compath.constants import DEFAULT_CACHE_CONNECTION

log = logging.getLogger(__name__)


def set_debug(level):
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")
    log.setLevel(level=level)


def set_debug_param(debug):
    if debug == 1:
        set_debug(20)
    elif debug == 2:
        set_debug(10)


@click.group()
def main():
    """ComPath"""
    logging.basicConfig(level=10, format="%(asctime)s - %(levelname)s - %(message)s")


@main.command()
@click.option('-v', '--debug', count=True, help="Turn on debugging.")
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
@click.option('-d', '--delete_first', is_flag=True)
def populate(debug, connection, delete_first):
    """Build the local version of Reactome/KEGG."""

    set_debug_param(debug)

    reactome_manager = ReactomeManager(connection=connection)
    kegg_manager = KeggManager(connection=connection)

    if delete_first or click.confirm('Drop first the Reactome database?'):
        reactome_manager.drop_all()
        reactome_manager.create_all()

    # Only human genes are used
    reactome_manager.populate(only_human=True)

    if delete_first or click.confirm('Drop first the KEGG database?'):
        kegg_manager.drop_all()
        kegg_manager.create_all()

    kegg_manager.populate()


@main.command()
@click.option('-v', '--debug', count=True, help="Turn on debugging.")
@click.option('-y', '--yes', is_flag=True)
@click.option('-c', '--connection', help='Defaults to {}'.format(DEFAULT_CACHE_CONNECTION))
def drop(debug, yes, connection):
    """Drop the Reactome/KEGG database."""

    set_debug_param(debug)

    if yes or click.confirm('Do you really want to delete the Reactome database?'):
        reactome_manager = ReactomeManager(connection=connection)
        click.echo("drop db")
        reactome_manager.drop_all()

    if yes or click.confirm('Do you really want to delete the KEGG database?'):
        kegg_manager = KeggManager(connection=connection)
        click.echo("drop db")
        kegg_manager.drop_all()


@main.command()
@click.option('-v', '--debug', count=True, help="Turn on debugging.")
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
def web(debug, connection):
    """Run web"""

    set_debug_param(debug)

    from compath.web import create_app
    app = create_app(connection=connection)
    app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
