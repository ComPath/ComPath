# -*- coding: utf-8 -*-

"""This module contains the main views of ComPath."""

import datetime
import logging
import sys

from flask import Blueprint, render_template
from flask_security import current_user, login_required

from ..constants import BLACKLIST, STYLED_NAMES
from ..state import bio2bel_managers, compath_state

logger = logging.getLogger(__name__)

time_instantiated = str(datetime.datetime.now())
ui_blueprint = Blueprint('ui', __name__)

"""Main Views"""


@ui_blueprint.route('/')
def home():
    """ComPath home page."""
    return render_template('home.html')


@ui_blueprint.route('/imprint')
def imprint():
    """Render the Imprint page."""
    return render_template('meta/imprint.html')


@ui_blueprint.route('/terms_and_conditions')
def terms_and_conditions():
    """Render the Terms and conditions page."""
    return render_template('meta/terms_conditions.html')


@ui_blueprint.route('/rdfs')
def rdf():
    """RDF about page."""
    return render_template('meta/rdf.html')


@ui_blueprint.route('/about')
def about():
    """Render About page."""
    metadata = [
        ('Python Version', sys.version),
        ('Deployed', time_instantiated),
    ]

    return render_template(
        'meta/about.html',
        metadata=metadata,
        db_version=compath_state.database_date,
        STYLED_NAMES=STYLED_NAMES,
    )


@ui_blueprint.route('/curation_protocol')
def curation_protocol():
    """Render Curation page."""
    return render_template('curation_protocol.html')


@ui_blueprint.route('/overview')
def overview():
    """Render Overview page."""
    return render_template(
        'overview.html',
        managers_overlap=compath_state.overlap,
        resource_overview=compath_state.resource_overview,
        managers=bio2bel_managers.keys(),
        distributions=compath_state.resource_to_pathway_distribution,
        db_version=compath_state.database_date,
        BLACK_LIST=BLACKLIST,
        STYLED_NAMES=STYLED_NAMES,
    )


@ui_blueprint.route('/similarity')
def similarity():
    """Render Similarity page."""
    return render_template('similarity.html')


@ui_blueprint.route('/user')
@login_required
def user_activity():
    """Render the user activity page."""
    return render_template('user/activity.html', user=current_user, STYLED_NAMES=STYLED_NAMES)


"""Clustergrammer views"""


@ui_blueprint.route('/kegg_overlap')
def kegg_matrix():
    """Render the KEGG Matrix page powered by Clustergrammer."""
    return render_template('visualization/clustergrammer/kegg_overlap.html')


@ui_blueprint.route('/reactome_overlap')
def reactome_matrix():
    """Render the Reactome Matrix page powered by Clustergrammer."""
    return render_template('visualization/clustergrammer/reactome_overlap.html')


@ui_blueprint.route('/wikipathways_overlap')
def wikipathways_matrix():
    """Render the WikiPathways Matrix page powered by Clustergrammer."""
    return render_template('visualization/clustergrammer/wikipathways_overlap.html')
