# -*- coding: utf-8 -*-

"""Command line interface."""

from __future__ import print_function

import datetime
import logging
import sys

import click
from flask_security import SQLAlchemyUserDatastore

from compath import managers
from compath.constants import ADMIN_EMAIL, DEFAULT_CACHE_CONNECTION
from compath.curation.hierarchies import load_hierarchy
from compath.curation.parser import parse_curation_template, parse_special_mappings
from compath.manager import Manager
from compath.models import Base, Role, User
from compath.utils import _iterate_user_strings

log = logging.getLogger(__name__)


def set_debug(level):
    """Set debug."""
    log.setLevel(level=level)


def set_debug_param(debug):
    """Set parameter."""
    if debug == 1:
        set_debug(20)
    elif debug == 2:
        set_debug(10)


@click.group(help='ComPath at {}'.format(DEFAULT_CACHE_CONNECTION))
def main():
    """Main click method"""
    logging.basicConfig(level=20, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")


@main.group()
@click.option('-c', '--connection', help='Cache connection. Defaults to {}'.format(DEFAULT_CACHE_CONNECTION))
@click.pass_context
def manage(ctx, connection):
    """Manage the database"""
    ctx.obj = Manager.from_connection(connection)
    Base.metadata.bind = ctx.obj.engine
    Base.query = ctx.obj.session.query_property()
    ctx.obj.create_all()


@manage.group()
def users():
    """User group"""
    pass


@main.command()
def ls():
    """Display registered Bio2BEL pathway managers."""
    for manager in managers:
        click.echo(manager)


@main.command()
@click.option('--host', default='0.0.0.0', help='Flask host. Defaults to 0.0.0.0')
@click.option('--port', type=int, default=5000, help='Flask port. Defaults to 5000')
@click.option('--template-folder', default='templates', help="Template folder. Defaults to 'templates'")
@click.option('--static-folder', default='static', help="Template folder. Defaults to 'static'")
@click.option('-v', '--debug', count=True, help="Turn on debugging.")
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
def web(host, port, template_folder, static_folder, debug, connection):
    """Run web service."""
    set_debug_param(debug)

    from compath.web import create_app
    app = create_app(connection=connection, template_folder=template_folder, static_folder=static_folder)
    app.run(host=host, port=port)


@main.command()
@click.option('-v', '--debug', count=True, help="Turn on debugging.")
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
@click.option('-d', '--delete-first', is_flag=True)
def populate(debug, connection, delete_first):
    """Populate all registered Bio2BEL pathway packages."""
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
    """Drop ComPath DB."""
    set_debug_param(debug)

    if yes or click.confirm('Do you really want to delete the ComPath DB'):
        m = Manager.from_connection(connection=connection)
        click.echo('Deleting ComPath DB')
        m.drop_all()
        m.create_all()


@main.command()
@click.option('-v', '--debug', count=True, help="Turn on debugging.")
@click.option('-y', '--yes', is_flag=True)
@click.option('-c', '--connection', help='Defaults to {}'.format(DEFAULT_CACHE_CONNECTION))
def drop_databases(debug, yes, connection):
    """Drop all databases."""
    set_debug_param(debug)

    if yes or click.confirm('Do you really want to delete the databases for {}?'.format(', '.join(managers))):
        for name, Manager in managers.items():
            m = Manager(connection=connection)
            click.echo('deleting {}'.format(name))
            m.drop_all()


@main.command()
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
def load_mappings(connection):
    """Load mappings from template."""
    set_debug_param(2)

    parse_curation_template(
        'https://github.com/ComPath/resources/raw/master/mappings/kegg_wikipathways.xlsx',
        'kegg',
        'wikipathways',
        curator_emails=['daniel.domingo.fernandez@scai.fraunhofer.de','carlos.bobis@scai.fraunhofer.de', 'josepmarinllao@gmail.com'],
        connection=connection
    )
    parse_curation_template(
        'https://github.com/ComPath/resources/raw/master/mappings/kegg_reactome.xlsx',
        'kegg',
        'reactome',
        curator_emails=['daniel.domingo.fernandez@scai.fraunhofer.de','carlos.bobis@scai.fraunhofer.de', 'josepmarinllao@gmail.com'],
        connection=connection
    )
    parse_curation_template(
        'https://github.com/ComPath/resources/raw/master/mappings/wikipathways_reactome.xlsx',
        'wikipathways',
        'reactome',
        curator_emails=['daniel.domingo.fernandez@scai.fraunhofer.de','carlos.bobis@scai.fraunhofer.de', 'josepmarinllao@gmail.com'],
        connection=connection
    )

    parse_special_mappings(
        'https://github.com/ComPath/resources/raw/master/mappings/special_mappings.xlsx',
        curator_emails=['daniel.domingo.fernandez@scai.fraunhofer.de','carlos.bobis@scai.fraunhofer.de', 'josepmarinllao@gmail.com'],
        connection=connection,
    )


@main.command()
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
@click.option('-e', '--email', help="Default curator: {}".format(ADMIN_EMAIL))
def load_hierarchies(connection, email):
    """Load pathway databases with hierarchies."""
    set_debug_param(2)

    # Example: python3 -m compath load_hierarchies --email='your@email.com'

    load_hierarchy(connection=connection, curator_email=email)


@users.command()
@click.pass_obj
def ls(manager):
    """Lists all users"""
    for s in _iterate_user_strings(manager):
        click.echo(s)


@users.command()
@click.argument('email')
@click.argument('password')
@click.pass_obj
def make_user(manager, email, password):
    """Create a pre-existing user an admin."""
    # Example: python3 -m compath make_admin xxx@xxx.com password

    ds = SQLAlchemyUserDatastore(manager, User, Role)
    user = ds.find_user(email=email)

    if user is None:
        ds.create_user(email=email, password=password, confirmed_at=datetime.datetime.utcnow())
        ds.commit()
        click.echo('User {} was successfully created'.format(email))

    else:
        click.echo('User {} already exists'.format(email))


@users.command()
@click.argument('email')
@click.pass_obj
def make_admin(manager, email):
    """Make a pre-existing user an admin."""
    # Example: python3 -m compath make_admin xxx@xxx.com

    ds = SQLAlchemyUserDatastore(manager, User, Role)
    user = ds.find_user(email=email)

    if user is None:
        click.echo('User not found')
        sys.exit(0)

    admin = ds.find_or_create_role('admin')

    ds.add_role_to_user(user, admin)
    ds.commit()
    click.echo('User {} is now admin'.format(email))


if __name__ == '__main__':
    main()
