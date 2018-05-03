# -*- coding: utf-8 -*-

"""This module contains the flask-admin application."""

import os
import time

from compath import managers
from compath.constants import BLACK_LIST, DEFAULT_CACHE_CONNECTION, SWAGGER_CONFIG
from compath.manager import Manager
from compath.models import Base, PathwayMapping, Role, User, Vote
from compath.views.analysis_service import analysis_blueprint
from compath.views.curation_service import curation_blueprint
from compath.views.db_service import db_blueprint
from compath.views.main_service import ui_blueprint
from compath.views.model_service import MappingView, VoteView
from compath.views.model_service import model_blueprint
from compath.visualization.venn_diagram import process_overlap_for_venn_diagram

import logging

from bio2bel_hgnc.manager import Manager as HgncManager
from flasgger import Swagger
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_bootstrap import Bootstrap
from flask_security import SQLAlchemyUserDatastore, Security
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

log = logging.getLogger(__name__)

bootstrap = Bootstrap()
security = Security()
swagger = Swagger()


def create_app(connection=None):
    """Create the Flask application.

    :type connection: Optional[str]
    :rtype: flask.Flask
    """
    t = time.time()

    app = Flask(__name__)

    @app.template_filter('remove_prefix')
    def remove_prefix(text, prefix):
        """Remove prefix from string.

        :param str text: string from which the prefix would be subtracted
        :param str prefix: prefix to delete
        :rtype: str
        """
        if text.startswith(prefix):
            return text[len(prefix):]
        return text

    app.config['SQLALCHEMY_DATABASE_URI'] = connection or DEFAULT_CACHE_CONNECTION
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
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

    app.config.setdefault('SWAGGER', SWAGGER_CONFIG)

    # TODO: Change for deployment. Create a new with 'os.urandom(24)'
    app.secret_key = 'a\x1c\xd4\x1b\xb1\x05\xac\xac\xee\xcb6\xd8\x9fl\x14%B\xd2W\x9fP\x06\xcb\xff'

    csrf = CSRFProtect(app)
    bootstrap.init_app(app)
    db = SQLAlchemy(app)

    class WebManager(Manager):
        """Web manager class."""

        def __init__(self):
            self.session = db.session
            self.engine = db.engine

        def drop_all(self):
            """Drop all tables for ComPath."""
            Base.metadata.drop_all(self.engine)
            Base.metadata.create_all(self.engine)

    app.manager = WebManager()

    with app.app_context():
        Base.metadata.bind = db.engine
        Base.query = db.session.query_property()

        try:
            db.create_all()
        except Exception:
            log.exception('Failed to create all')

    user_datastore = SQLAlchemyUserDatastore(app.manager, User, Role)

    security.init_app(app, user_datastore)
    swagger.init_app(app)

    admin = Admin(app, template_mode='bootstrap3')
    admin.add_view(ModelView(User, app.manager.session))
    admin.add_view(ModelView(Role, app.manager.session))
    admin.add_view(MappingView(PathwayMapping, app.manager.session))
    admin.add_view(VoteView(Vote, app.manager.session))

    app.register_blueprint(ui_blueprint)
    app.register_blueprint(curation_blueprint)
    app.register_blueprint(model_blueprint)
    app.register_blueprint(analysis_blueprint)
    app.register_blueprint(db_blueprint)

    app.manager_dict = {
        name: ExternalManager(connection=connection)
        for name, ExternalManager in managers.items()
    }

    log.info('Loading pathway distributions')

    app.resource_distributions = {
        name: manager.get_pathway_size_distribution()
        for name, manager in app.manager_dict.items()
        if name not in BLACK_LIST
    }

    log.info('Loading gene distributions')

    app.gene_distributions = {
        name: dict(manager.get_gene_distribution())
        for name, manager in app.manager_dict.items()
        if name not in BLACK_LIST
    }

    log.info('Loading overlap across pathway databases')

    resource_gene_sets = {
        name: manager.get_all_hgnc_symbols()
        for name, manager in app.manager_dict.items()
        if name not in BLACK_LIST
    }

    log.info('Loading resource overview')

    app.resource_overview = {
        name: (len(manager.get_all_pathways()), len(resource_gene_sets[name]))
        # dict(Manager name: tuple(#pathways, #genes))
        for name, manager in app.manager_dict.items()
        if name not in BLACK_LIST
    }

    # Get the universe of all HGNC symbols from Bio2BEL_hgnc and close the session
    log.info('Loading gene universe from bio2BEL_hgnc ')

    hgnc_manager = HgncManager()

    resource_gene_sets['Gene Universe'] = hgnc_manager.get_all_hgnc_symbols()

    app.gene_universe = resource_gene_sets['Gene Universe']

    if len(resource_gene_sets['Gene Universe']) < 40000:
        log.warning(
            'The number of HGNC symbols loaded is smaller than 40000. Please check that HGNC database has been'
            'properly loaded'
        )

    app.manager_overlap = process_overlap_for_venn_diagram(gene_sets=resource_gene_sets, skip_gene_set_info=True)

    hgnc_manager.session.close()

    log.info('Done building %s in %.2f seconds', app, time.time() - t)

    return app


if __name__ == '__main__':
    app_ = create_app()
    app_.run(debug=True, host='0.0.0.0', port=5000)
