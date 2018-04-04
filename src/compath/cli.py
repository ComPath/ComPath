# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
import logging
import sys

import click
from flask_security import SQLAlchemyUserDatastore

from . import managers
from .constants import DEFAULT_CACHE_CONNECTION
from .curation.curation import parse_curation_template
from .manager import RealManager
from .models import Base, Role, User

log = logging.getLogger(__name__)


def set_debug(level):
    log.setLevel(level=level)


def set_debug_param(debug):
    if debug == 1:
        set_debug(20)
    elif debug == 2:
        set_debug(10)


@click.group(help='ComPath at {}'.format(DEFAULT_CACHE_CONNECTION))
def main():
    logging.basicConfig(level=10, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")


@main.command()
def ls():
    """Display registered Bio2BEL pathway managers"""
    for manager in managers:
        click.echo(manager)


@main.command()
@click.option('-v', '--debug', count=True, help="Turn on debugging.")
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
@click.option('-d', '--delete-first', is_flag=True)
def populate(debug, connection, delete_first):
    """Populate all registered Bio2BEL pathway packages"""
    set_debug_param(debug)

    for name, Manager in managers.items():
        m = Manager(connection=connection)
        log.info('populating %s at %s', name, m.engine.url)

        if delete_first:
            click.echo('deleting {}'.format(name))
            m.drop_all()
            m.create_all()

        click.echo('populating {}'.format(name))
        m.populate()


@main.command()
@click.option('-v', '--debug', count=True, help="Turn on debugging.")
@click.option('-y', '--yes', is_flag=True)
@click.option('-c', '--connection', help='Defaults to {}'.format(DEFAULT_CACHE_CONNECTION))
def drop(debug, yes, connection):
    """Drop all databases"""
    set_debug_param(debug)

    if yes or click.confirm('Do you really want to delete the ComPath DB'):
        m = RealManager(connection=connection)
        click.echo('Deleting ComPath DB')
        m.drop_all()
        m.create_all()


@main.command()
@click.option('-v', '--debug', count=True, help="Turn on debugging.")
@click.option('-y', '--yes', is_flag=True)
@click.option('-c', '--connection', help='Defaults to {}'.format(DEFAULT_CACHE_CONNECTION))
def drop_databases(debug, yes, connection):
    """Drop all databases"""
    set_debug_param(debug)

    if yes or click.confirm('Do you really want to delete the databases for {}?'.format(', '.join(managers))):
        for name, Manager in managers.items():
            m = Manager(connection=connection)
            click.echo('deleting {}'.format(name))
            m.drop_all()


@main.command()
@click.argument('path')
@click.argument('reference')
@click.argument('compare')
def add_mappings(path, reference, compare):
    """Add mappings from template"""

    # Example: python3 -m compath add_mappings '/my/path' 'kegg' 'wikipathways'

    set_debug_param(2)

    parse_curation_template(path, reference, compare)


@main.command()
@click.argument('email')
@click.argument('password')
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
def make_user(connection, email, password):
    """Makes a pre-existing user an admin"""

    # Example: python3 -m compath make_admin xxx@xxx.com

    manager = RealManager(connection=connection)
    Base.metadata.bind = manager.engine
    Base.query = manager.session.query_property()
    manager.create_all()

    ds = SQLAlchemyUserDatastore(manager, User, Role)
    user = ds.find_user(email=email)

    if user is None:
        user = User(email=email, password=password, confirmed_at=datetime.datetime.utcnow())
        ds.commit()


@main.command()
@click.argument('email')
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
def make_admin(connection, email):
    """Makes a pre-existing user an admin"""

    # Example: python3 -m compath make_admin xxx@xxx.com

    manager = RealManager(connection=connection)
    Base.metadata.bind = manager.engine
    Base.query = manager.session.query_property()
    manager.create_all()

    ds = SQLAlchemyUserDatastore(manager, User, Role)
    user = ds.find_user(email=email)

    if user is None:
        click.echo('Not user found')
        sys.exit(0)

    admin = ds.find_or_create_role('admin')

    ds.add_role_to_user(user, admin)
    ds.commit()


if __name__ == '__main__':
    main()
