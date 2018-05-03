# -*- coding: utf-8 -*-

"""This module contains the main views of ComPath."""

import datetime
import sys

import logging

from compath.constants import BLACK_LIST

from flask import (
    Blueprint,
    current_app,
    render_template
)
from flask_security import current_user, login_required

log = logging.getLogger(__name__)
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
    return render_template('imprint.html')


@ui_blueprint.route('/terms_and_conditions')
def terms_and_conditions():
    """Render the Terms and conditiosn page."""
    return render_template('terms_conditions.html')


@ui_blueprint.route('/about')
def about():
    """Render About page."""
    metadata = [
        ('Python Version', sys.version),
        ('Deployed', time_instantiated)
    ]

    return render_template('about.html', metadata=metadata)


@ui_blueprint.route('/curation_protocol')
def curation_protocol():
    """Render Curation page."""
    return render_template('curation_protocol.html')


@ui_blueprint.route('/overview')
def overview():
    """Render Overview page."""
    return render_template(
        'overview.html',
        managers_overlap=current_app.manager_overlap,
        resource_overview=current_app.resource_overview,
        managers=current_app.manager_dict.keys(),
        distributions=current_app.resource_distributions,
        BLACK_LIST=BLACK_LIST
    )


@ui_blueprint.route('/similarity')
def similarity():
    """Render Similarity page."""
    return render_template('similarity.html')


@ui_blueprint.route('/user')
@login_required
def user_activity():
    """Render the user activity page."""
    return render_template('user/activity.html', user=current_user)


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
