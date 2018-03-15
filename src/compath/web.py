# -*- coding: utf-8 -*-

""" This module contains the flask-admin application to visualize the db"""

import logging
import os
import time

from bio2bel_hgnc.manager import Manager as HgncManager
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_bootstrap import Bootstrap
from flask_security import SQLAlchemyUserDatastore, Security
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from . import managers
from .constants import DEFAULT_CACHE_CONNECTION
from .main_service import ui_blueprint
from .manager import Manager
from .models import Base, Mapping, Role, User, Vote
from .utils import process_overlap_for_venn_diagram

log = logging.getLogger(__name__)

bootstrap = Bootstrap()
security = Security()
db = SQLAlchemy()


def create_app(connection=None):
    """Creates a Flask application

    :type connection: Optional[str]
    :rtype: flask.Flask
    """
    t = time.time()

    app = Flask(__name__)

    @app.template_filter('remove_prefix')
    def remove_prefix(text, prefix):
        """Remove prefix from string

        :param str text: string from which the prefix would be subtracted
        :param str prefix: prefix to delete
        :rtype: str
        """
        if text.startswith(prefix):
            return text[len(prefix):]
        return text

    app.config['SQLALCHEMY_DATABASE_URI'] = connection or DEFAULT_CACHE_CONNECTION

    app.config.update(
        SECURITY_REGISTERABLE=True,
        SECURITY_CONFIRMABLE=False,
        SECURITY_SEND_REGISTER_EMAIL=False,
        SECURITY_RECOVERABLE=True,
        #: What hash algorithm should we use for passwords
        SECURITY_PASSWORD_HASH='pbkdf2_sha512',
        #: What salt should we use to hash passwords? DEFINITELY CHANGE THIS
        SECURITY_PASSWORD_SALT=os.environ.get('COMPATH_SECURITY_PASSWORD_SALT', 'compath_not_default_salt1234567890')
    )

    # TODO: Change for deployment. Create a new with 'os.urandom(24)'
    app.secret_key = 'a\x1c\xd4\x1b\xb1\x05\xac\xac\xee\xcb6\xd8\x9fl\x14%B\xd2W\x9fP\x06\xcb\xff'

    csrf = CSRFProtect(app)
    bootstrap.init_app(app)

    db.init_app(app)

    class WebManager(Manager):
        def __init__(self):
            self.session = db.session
            self.engine = db.session

    manager = WebManager()

    with app.app_context():
        Base.metadata.bind = db.engine
        Base.query = db.session.query_property()

        try:
            manager.create_all()
        except Exception:
            log.exception('Failed to create all')

    user_datastore = SQLAlchemyUserDatastore(manager, User, Role)

    security.init_app(app, user_datastore)

    admin = Admin(app, template_mode='bootstrap3')
    admin.add_view(ModelView(User, manager.session))
    admin.add_view(ModelView(Role, manager.session))
    admin.add_view(ModelView(Mapping, manager.session))
    admin.add_view(ModelView(Vote, manager.session))

    app.register_blueprint(ui_blueprint)

    app.manager_dict = {
        name: ExternalManager(connection=connection)
        for name, ExternalManager in managers.items()
    }

    log.info('Loading resource distributions')

    # app.resource_distributions = {
    #     name: manager.get_pathway_size_distribution()
    #     for name, manager in app.manager_dict.items()
    # }
    #
    log.info('Loading overlap across pathway databases')

    resource_genesets = {}
    #
    # for name, manager in app.manager_dict.items():
    #
    #     if name == 'compath_hgnc':
    #         name = 'hgnc families'
    #
    #     resource_genesets[name] = manager.get_all_hgnc_symbols()
    #
    # # Get the universe of all HGNC symbols from Bio2BEL_hgnc and close the session
    # log.info('Loading gene universe from bio2BEL_hgnc ')
    # # TODO Uncomment later
    hgnc_manager = HgncManager()

    resource_genesets['Gene Universe'] = hgnc_manager.get_all_hgnc_symbols()

    app.gene_universe = len(resource_genesets['Gene Universe'])

    if app.gene_universe < 40000:
        log.warning(
            'The number of HGNC symbols loaded is smaller than 40000. Please check that HGNC database has been'
            'properly loaded'
        )

    app.manager_overlap = process_overlap_for_venn_diagram(gene_sets=resource_genesets, skip_gene_set_info=True)

    hgnc_manager.session.close()

    log.info('Done building %s in %.2f seconds', app, time.time() - t)

    return app


if __name__ == '__main__':
    app_ = create_app()
    app_.run(debug=True, host='0.0.0.0', port=5000)
