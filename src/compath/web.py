# -*- coding: utf-8 -*-

"""This module contains the ComPath web application."""

import logging
import os
import time
import typing
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple

from flasgger import Swagger
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_bootstrap import Bootstrap
from flask_security import SQLAlchemyUserDatastore, Security
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from bio2bel.compath import CompathManager, get_compath_managers
from pyobo import get_id_name_mapping
from .constants import BLACKLIST, DEFAULT_CACHE_CONNECTION, PATHME, SWAGGER_CONFIG
from .manager import Manager
from .models import Base, PathwayMapping, Role, User, Vote
from .pathme_ext import add_pathme
from .state import CompathState
from .utils import get_last_action_in_module, process_overlap_for_venn_diagram, simulate_pathway_enrichment
from .views.analysis_service import analysis_blueprint
from .views.api_service import api_blueprint
from .views.curation_service import curation_blueprint
from .views.db_service import db_blueprint
from .views.main_service import ui_blueprint
from .views.model_service import MappingView, VoteView, model_blueprint

logger = logging.getLogger(__name__)

bootstrap = Bootstrap()
security = Security()
swagger = Swagger()


class ComPathSQLAlchemy(SQLAlchemy):
    """ComPath."""

    manager: Manager = None

    def init_app(self, app):
        """Overwrite init app method."""
        super().init_app(app)
        self.manager = Manager(engine=self.engine, session=self.session)


def create_app(
    connection: Optional[str] = None,
    template_folder: Optional[str] = None,
    static_folder: Optional[str] = None,
) -> Flask:
    """Create the Flask application."""
    t = time.time()

    app = Flask(
        __name__,
        template_folder=template_folder or 'templates',
        static_folder=static_folder or 'static',
    )

    @app.template_filter('remove_prefix')
    def remove_prefix(text: str, prefix: str) -> str:
        """Remove prefix from string.

        :param text: string from which the prefix would be subtracted
        :param prefix: prefix to delete
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
    # app.secret_key = 'a\x1c\xd4\x1b\xb1\x05\xac\xac\xee\xcb6\xd8\x9fl\x14%B\xd2W\x9fP\x06\xcb\xff'
    app.secret_key = os.urandom(24)

    CSRFProtect(app)
    bootstrap.init_app(app)
    db = ComPathSQLAlchemy(app)

    logger.info('using connection at %s', db.engine.url)

    Base.metadata.bind = db.engine
    Base.query = db.session.query_property()
    db.create_all()

    user_datastore = SQLAlchemyUserDatastore(db.manager, User, Role)
    security.init_app(app, user_datastore)
    swagger.init_app(app)

    admin = Admin(app, template_mode='bootstrap3')
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Role, db.session))
    admin.add_view(MappingView(PathwayMapping, db.session))
    admin.add_view(VoteView(Vote, db.session))

    app.register_blueprint(ui_blueprint)
    app.register_blueprint(curation_blueprint)
    app.register_blueprint(model_blueprint)
    app.register_blueprint(analysis_blueprint)
    app.register_blueprint(db_blueprint)
    app.register_blueprint(api_blueprint)

    if PATHME:  # If PathMe-Viewer is installed, import its views
        add_pathme(app=app, admin=admin, db=db)

    bio2bel_managers: Mapping[str, CompathManager] = get_compath_managers(engine=db.engine, session=db.session)

    logger.info('Loading pathway database information')
    # Get the last time the database was populated
    database_date: Dict[str, str] = dict(_get_dates(bio2bel_managers))
    logger.info('Info: %s', database_date)

    logger.info('Loading pathway distributions')
    resource_to_pathway_distribution: Mapping[str, typing.Counter[str]] = {
        prefix: manager.get_pathway_size_distribution()
        for prefix, manager in bio2bel_managers.items()
        if prefix not in BLACKLIST
    }

    logger.info('Loading gene distributions')
    resource_to_gene_distribution: Mapping[str, typing.Counter[str]] = {
        prefix: manager.get_hgnc_id_size_distribution()
        for prefix, manager in bio2bel_managers.items()
        if prefix not in BLACKLIST
    }

    logger.info('Loading gene sets')
    resource_to_gene_sets: Mapping[str, Mapping[str, Set[str]]] = {
        prefix: manager.get_pathway_name_to_hgnc_symbols()
        for prefix, manager in bio2bel_managers.items()
        if prefix not in BLACKLIST
    }

    logger.info('Loading overlap across pathway databases')
    # Flat all genes in all pathways in each resource to calculate overlap at the database level
    resource_to_all_genes: Dict[str, Set[str]] = {
        prefix: {
            gene
            for genes in pathways.values()
            for gene in genes
        }
        for prefix, pathways in resource_to_gene_sets.items()
    }

    # TODO: select the databases (resource) to compare in the simulation
    simulate_resources = ['kegg', 'reactome', 'wikipathways']

    logger.info('Performing simulation with %s', simulate_resources)
    common_genes_simulated_resources: Set[str] = set.intersection(*[
        gene_set
        for resource_name, gene_set in resource_to_all_genes.items()
        if resource_name in simulate_resources
    ])
    _filtered_resource_gene_sets: Mapping[str, Mapping[str, Set[str]]] = {
        resource_name: value
        for resource_name, value in resource_to_gene_sets.items()
        if resource_name in simulate_resources
    }
    simulation_results: Mapping[str, List[float]] = simulate_pathway_enrichment(
        _filtered_resource_gene_sets,
        common_genes_simulated_resources,
        runs=200,
    )

    logger.info('Loading resource overview')
    resource_overview: Mapping[str, Tuple[int, int]] = {
        resource_name: (
            len(pathways),
            len(resource_to_all_genes[resource_name]),
        )
        for resource_name, pathways in resource_to_gene_sets.items()
    }

    logger.info('Loading gene universe')
    resource_to_all_genes['Gene Universe'] = set(get_id_name_mapping('hgnc'))
    if len(resource_to_all_genes['Gene Universe']) < 40000:
        logger.warning(
            'The number of HGNC symbols loaded is smaller than 40000. Please check that HGNC database has been'
            'properly loaded'
        )

    logger.info('generating gene set overlap venn diagram')
    overlap: List[Mapping[str, Any]] = process_overlap_for_venn_diagram(
        gene_sets=resource_to_all_genes,
        skip_gene_set_info=True,
    )

    app.extensions['compath'] = CompathState(
        compath_manager=db.manager,
        user_datastore=user_datastore,
        bio2bel_managers=bio2bel_managers,
        overlap=overlap,
        database_date=database_date,
        resource_to_gene_distribution=resource_to_gene_distribution,
        resource_to_pathway_distribution=resource_to_pathway_distribution,
        simulation_results=simulation_results,
        resource_overview=resource_overview,
    )

    logger.info('Done building %s in %.2f seconds', app, time.time() - t)

    return app


def _get_dates(managers: Iterable[str]) -> Iterable[Tuple[str, str]]:
    for prefix in managers:
        action = get_last_action_in_module(prefix, 'populate')
        date = (
            action.created.strftime("%Y-%m-%d %H:%M:%S")
            if action else
            'Empty'
        )
        yield prefix, date


if __name__ == '__main__':
    app_ = create_app()
    app_.run(host='0.0.0.0', port=5000)
