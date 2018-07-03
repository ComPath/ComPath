# -*- coding: utf-8 -*-

"""This module contains the flask-admin application."""

import logging
import os
import time
from functools import reduce
from operator import and_

from bio2bel_hgnc.manager import Manager as HgncManager
from flasgger import Swagger
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_bootstrap import Bootstrap
from flask_security import SQLAlchemyUserDatastore, Security
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from compath import managers
from compath.constants import BLACK_LIST, DEFAULT_CACHE_CONNECTION, SWAGGER_CONFIG
from compath.manager import Manager
from compath.models import Base, PathwayMapping, Role, User, Vote
from compath.utils import simulate_pathway_enrichment
from compath.views.analysis_service import analysis_blueprint
from compath.views.api_service import api_blueprint
from compath.views.curation_service import curation_blueprint
from compath.views.db_service import db_blueprint
from compath.views.main_service import ui_blueprint
from compath.views.model_service import MappingView, VoteView, model_blueprint
from compath.visualization.venn_diagram import process_overlap_for_venn_diagram

log = logging.getLogger(__name__)

bootstrap = Bootstrap()
security = Security()
swagger = Swagger()


class ComPathSQLAlchemy(SQLAlchemy):
    """ComPath"""

    def init_app(self, app):
        """Overwrite init app method."""
        super().init_app(app)

        self.manager = Manager(engine=self.engine, session=self.session)


def create_app(connection=None, template_folder='templates', static_folder='static'):
    """Create the Flask application.

    :type connection: Optional[str]
    :rtype: flask.Flask
    """
    t = time.time()

    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

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

    CSRFProtect(app)
    bootstrap.init_app(app)
    db = ComPathSQLAlchemy(app)

    with app.app_context():
        Base.metadata.bind = db.engine
        Base.query = db.session.query_property()

        try:
            db.create_all()
        except Exception:
            log.exception('Failed to create all')

    app.manager = db.manager

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
    app.register_blueprint(api_blueprint)

    app.manager_dict = {
        resource_name: ExternalManager(connection=connection)
        for resource_name, ExternalManager in managers.items()
    }

    log.info('Loading pathway distributions')

    app.resource_distributions = {
        resource_name: manager.get_pathway_size_distribution()
        for resource_name, manager in app.manager_dict.items()
        if resource_name not in BLACK_LIST
    }

    log.info('Loading gene distributions')
    # TODO @cthoyt too slow
    app.gene_distributions = {
        resource_name: dict(manager.get_gene_distribution())
        for resource_name, manager in app.manager_dict.items()
        if resource_name not in BLACK_LIST
    }

    log.info('Loading gene sets')
    resource_gene_sets = {
        resource_name: manager.export_gene_sets()
        for resource_name, manager in app.manager_dict.items()
        if resource_name not in BLACK_LIST
    }

    log.info('Loading overlap across pathway databases')
    # Flat all genes in all pathways in each resource to calculate overlap at the database level
    resource_all_genes = {
        resource: {
            gene
            for pathway, genes in pathways.items()
            for gene in genes
        }
        for resource, pathways in resource_gene_sets.items()
    }

    # TODO: select the databases (resource) to compare in the simulation
    simulate_resources = ['kegg', 'reactome', 'wikipathways']

    if resource_all_genes:
        log.info('Performing simulation with {}'.format(simulate_resources))

        common_genes_simulated_resources = reduce(and_, [
            gene_set
            for resource_name, gene_set in resource_all_genes.items()
            if resource_name in simulate_resources
        ])

        app.simulation_results = simulate_pathway_enrichment(
            {
                resource_name: value
                for resource_name, value in resource_gene_sets.items()
                if resource_name in simulate_resources
            },
            common_genes_simulated_resources,
            runs=200
        )

    else:
        log.warning('No data has been fetched')

    log.info('Loading resource overview')
    app.resource_overview = {
        resource_name: (len(pathways), len(resource_all_genes[resource_name]))
        # dict(Manager resource name: tuple(#pathways, #genes))
        for resource_name, pathways in resource_gene_sets.items()
    }

    # Get the universe of all HGNC symbols from Bio2BEL_hgnc and close the session
    log.info('Loading gene universe from bio2BEL_hgnc ')

    hgnc_manager = HgncManager(connection=connection)

    resource_all_genes['Gene Universe'] = hgnc_manager.get_all_hgnc_symbols()

    app.gene_universe = resource_all_genes['Gene Universe']

    if len(resource_all_genes['Gene Universe']) < 40000:
        log.warning(
            'The number of HGNC symbols loaded is smaller than 40000. Please check that HGNC database has been'
            'properly loaded'
        )

    app.manager_overlap = process_overlap_for_venn_diagram(gene_sets=resource_all_genes, skip_gene_set_info=True)

    hgnc_manager.session.close()

    log.info('Done building %s in %.2f seconds', app, time.time() - t)

    return app


if __name__ == '__main__':
    app_ = create_app()
    app_.run(debug=True, host='0.0.0.0', port=5000)
