# -*- coding: utf-8 -*-

""" This module contains the main views of ComPath"""

import logging
import sys

import datetime
from flask import (
    Blueprint,
    render_template,
    current_app
)
from flask_security import login_required, current_user

log = logging.getLogger(__name__)
time_instantiated = str(datetime.datetime.now())
ui_blueprint = Blueprint('ui', __name__)

"""Main Views"""


@ui_blueprint.route('/')
def home():
    """ComPath home page"""
    return render_template('home.html')


@ui_blueprint.route('/imprint')
def imprint():
    """Renders the Imprint page"""
    return render_template('imprint.html')


@ui_blueprint.route('/about')
def about():
    """Renders About page"""
    metadata = [
        ('Python Version', sys.version),
        ('Deployed', time_instantiated)
    ]

    return render_template('about.html', metadata=metadata)


@ui_blueprint.route('/curation')
def curation():
    """Renders Curation page"""
    return render_template('curation.html')


@ui_blueprint.route('/overview')
def overview():
    """Renders Overview page"""
    return render_template(
        'overview.html',
        managers_overlap=current_app.manager_overlap,
        resource_overview=current_app.resource_overview
    )


@ui_blueprint.route('/similarity')
def similarity():
    """Renders Similarity page"""
    return render_template('similarity.html')


@ui_blueprint.route('/user')
@login_required
def user_activity():
    """Renders the user activity page"""
    return render_template('user/activity.html', user=current_user)


"""Clustergrammer views"""


@ui_blueprint.route('/kegg_overlap')
def kegg_matrix():
    """Renders the KEGG Matrix page powered by Clustergrammer"""
    return render_template('visualization/clustergrammer/kegg_overlap.html')


@ui_blueprint.route('/reactome_overlap')
def reactome_matrix():
    """Renders the Reactome Matrix page powered by Clustergrammer"""
    return render_template('visualization/clustergrammer/reactome_overlap.html')


@ui_blueprint.route('/wikipathways_overlap')
def wikipathways_matrix():
    """Renders the WikiPathways Matrix page powered by Clustergrammer"""
    return render_template('visualization/clustergrammer/wikipathways_overlap.html')


@ui_blueprint.route('/msig_overlap')
def msig_matrix():
    """Renders the WikiPathways Matrix page powered by Clustergrammer"""
    return render_template('visualization/clustergrammer/msig_overlap.html')
