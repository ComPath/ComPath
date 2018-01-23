# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
import os

import click

from compath.constants import DEFAULT_CACHE_CONNECTION
from bio2bel_reactome.manager import Manager
from bio2bel_reactome.to_belns import deploy_to_arty
from bio2bel_reactome.utils import dict_to_pandas_df

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
    """Reactome to BEL"""
    logging.basicConfig(level=10, format="%(asctime)s - %(levelname)s - %(message)s")


@main.command()
@click.option('-v', '--debug', count=True, help="Turn on debugging.")
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
@click.option('-d', '--delete_first', is_flag=True)
@click.option('-only-human', '--only_human', help="Set --only_human=True to store only human proteins in the DB.")
def populate(debug, connection, delete_first, only_human):
    """Build the local version of the full Reactome."""

    set_debug_param(debug)

    m = Manager(connection=connection)

    if delete_first or click.confirm('Drop first the database?'):
        m.drop_all()
        m.create_all()

    m.populate(only_human=only_human)


@main.command()
@click.option('-v', '--debug', count=True, help="Turn on debugging.")
@click.option('-y', '--yes', is_flag=True)
@click.option('-c', '--connection', help='Defaults to {}'.format(DEFAULT_CACHE_CONNECTION))
def drop(debug, yes, connection):
    """Drop the Reactome database."""

    set_debug_param(debug)

    if yes or click.confirm('Do you really want to delete the database?'):
        m = Manager(connection=connection)
        click.echo("drop db")
        m.drop_all()


@main.command()
@click.option('--force', is_flag=True, help="Force knowledge to be uploaded even if not new namespace")
def deploy(force):
    """Deploy to Artifactory"""
    deploy_to_arty(not force)


@main.command()
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
def export(connection):
    """Export all pathway - gene info to a excel file"""
    m = Manager(connection=connection)

    log.info("Querying the database")

    genesets = dict_to_pandas_df(m.export_genesets())

    log.info("Geneset exported to '{}/genesets.csv'".format(os.getcwd()))

    genesets.to_csv('genesets.csv', index=False)


@main.command()
@click.option('-v', '--debug', count=True, help="Turn on debugging.")
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
def web(debug, connection):
    """Run web"""

    set_debug_param(debug)

    from bio2bel_reactome.web import create_app
    app = create_app(connection=connection)
    app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
