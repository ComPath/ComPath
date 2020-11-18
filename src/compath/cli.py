# -*- coding: utf-8 -*-

"""Command line interface."""

import datetime
import sys
from typing import Optional

import click
from flask_security import SQLAlchemyUserDatastore

from bio2bel.compath import get_compath_manager_classes, get_compath_managers, iter_compath_managers
from pyobo.cli_utils import verbose_option
from .constants import ADMIN_EMAIL, DEFAULT_CACHE_CONNECTION
from .curation.hierarchies import load_hierarchy
from .curation.parser import parse_curation_template, parse_special_mappings
from .manager import Manager
from .models import Base, Role, User
from .utils import _iterate_user_strings

connection_option = click.option(
    '-c', '--connection',
    default=DEFAULT_CACHE_CONNECTION,
    show_default=True,
)


@click.group(help='ComPath at {}'.format(DEFAULT_CACHE_CONNECTION))
def main():
    """Start main click method."""


@main.group()
@connection_option
@click.pass_context
def manage(ctx, connection):
    """Manage the database."""
    ctx.obj = Manager.from_connection(connection)
    Base.metadata.bind = ctx.obj.engine
    Base.query = ctx.obj.session.query_property()
    ctx.obj.create_all()


@manage.group()
def users():
    """User group."""


@main.command()
def ls():
    """Display registered Bio2BEL pathway managers."""
    for manager in get_compath_manager_classes():
        click.echo(manager)


@main.command()
@connection_option
def summarize(connection: Optional[str]):
    """Summarize the contents."""
    for name, manager in iter_compath_managers(connection=connection):
        click.secho(name, bold=True, fg='magenta')
        for k, v in sorted(manager.summarize().items()):
            click.echo(f'  {k}: {v}')


@main.command()
@click.option('--host', default='0.0.0.0', help='Flask host. Defaults to 0.0.0.0')
@click.option('--port', type=int, default=5000, help='Flask port. Defaults to 5000')
@click.option('--template-folder', help="Template folder. Defaults to 'templates'")
@click.option('--static-folder', help="Template folder. Defaults to 'static'")
@verbose_option
@connection_option
def web(host, port, template_folder, static_folder, connection):
    """Run web service."""
    from .web import create_app
    app = create_app(
        connection=connection,
        template_folder=template_folder,
        static_folder=static_folder,
    )
    app.run(host=host, port=port)


@main.command()
@verbose_option
@connection_option
@click.option('-d', '--delete-first', is_flag=True)
def populate(connection: Optional[str], delete_first: bool):
    """Populate all registered Bio2BEL pathway packages."""
    for name, manager in iter_compath_managers(connection=connection):
        click.echo(f'populating {name} at {manager.engine.url}')

        if manager.is_populated():
            click.echo(f'already populated {name}')
            continue

        if delete_first:
            click.echo(f'deleting {name}')
            manager.drop_all()
            manager.create_all()

        click.echo(f'populating {name}')
        manager.populate()


@main.command()
@verbose_option
@click.option('-y', '--yes', is_flag=True)
@connection_option
def drop(yes: bool, connection: Optional[str]):
    """Drop ComPath DB."""
    if yes or click.confirm('Do you really want to delete the ComPath DB'):
        manager = Manager.from_connection(connection=connection)
        click.echo('Deleting ComPath DB')
        manager.drop_all()
        manager.create_all()


@main.command()
@verbose_option
@click.option('-y', '--yes', is_flag=True)
@connection_option
def drop_databases(yes: bool, connection: Optional[str]):
    """Drop all databases."""
    managers = get_compath_managers(connection=connection)
    if yes or click.confirm('Do you really want to delete the databases for {}?'.format(', '.join(managers))):
        for name, manager in managers.items():
            click.echo(f'deleting {name}')
            manager.drop_all()


@main.command()
@verbose_option
@connection_option
def load_mappings(connection: Optional[str]):
    """Load mappings from template."""
    compath_manager = Manager.from_connection(connection=connection)
    bio2bel_managers = get_compath_managers(connection=connection)

    parse_special_mappings(
        'https://github.com/ComPath/compath-resources/raw/master/mappings/special_mappings.csv',
        curator_emails=[
            'daniel.domingo.fernandez@scai.fraunhofer.de',
            'carlos.bobis@scai.fraunhofer.de',
            'josepmarinllao@gmail.com',
        ],
        compath_manager=compath_manager,
        bio2bel_managers=bio2bel_managers,
    )
    parse_curation_template(
        'https://github.com/ComPath/resources/raw/master/mappings/kegg_wikipathways.csv',
        'kegg',
        'wikipathways',
        curator_emails=[
            'daniel.domingo.fernandez@scai.fraunhofer.de',
            'carlos.bobis@scai.fraunhofer.de',
            'josepmarinllao@gmail.com',
        ],
        compath_manager=compath_manager,
        bio2bel_managers=bio2bel_managers,
    )
    parse_curation_template(
        'https://github.com/ComPath/resources/raw/master/mappings/kegg_reactome.csv',
        'kegg',
        'reactome',
        curator_emails=[
            'daniel.domingo.fernandez@scai.fraunhofer.de',
            'carlos.bobis@scai.fraunhofer.de',
            'josepmarinllao@gmail.com',
        ],
        compath_manager=compath_manager,
        bio2bel_managers=bio2bel_managers,
    )
    parse_curation_template(
        'https://github.com/ComPath/resources/raw/master/mappings/wikipathways_reactome.csv',
        'wikipathways',
        'reactome',
        curator_emails=[
            'daniel.domingo.fernandez@scai.fraunhofer.de',
            'carlos.bobis@scai.fraunhofer.de',
            'josepmarinllao@gmail.com',
        ],
        compath_manager=compath_manager,
        bio2bel_managers=bio2bel_managers,
    )


@main.command()
@connection_option
@click.option('-e', '--email', default=ADMIN_EMAIL, show_default=True)
@verbose_option
def load_hierarchies(connection: Optional[str], email: str):
    """Load pathway databases with hierarchies."""
    # Example: python3 -m compath load_hierarchies --email='your@email.com'
    load_hierarchy(connection=connection, curator_email=email)


@users.command()
@click.pass_obj
def ls(manager):
    """List all users."""
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
