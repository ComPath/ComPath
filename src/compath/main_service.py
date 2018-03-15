# -*- coding: utf-8 -*-

""" This module contains the main views of ComPath"""

import datetime
import logging
import sys

from flask import (
    Blueprint,
    render_template,
    current_app
)
from flask_security import login_required

log = logging.getLogger(__name__)
time_instantiated = str(datetime.datetime.now())
ui_blueprint = Blueprint('ui', __name__)

"""Main Views"""


@ui_blueprint.route('/', methods=['GET'])
def home():
    """ComPath home page"""
    return render_template('home.html')


@ui_blueprint.route('/imprint', methods=['GET'])
def imprint():
    """Renders the Imprint page"""
    return render_template('imprint.html')


@ui_blueprint.route('/about', methods=['GET'])
def about():
    """Renders About page"""
    metadata = [
        ('Python Version', sys.version),
        ('Deployed', time_instantiated)
    ]

    return render_template('about.html', metadata=metadata)


@ui_blueprint.route('/user', methods=['GET'])
@login_required
def user_activity():
    """Renders the user activity page"""
    return render_template('user/activity.html')





"""Clustergrammer views"""


@ui_blueprint.route('/kegg_overlap', methods=['GET'])
def kegg_matrix():
    """Renders the KEGG Matrix page powered by Clustergrammer"""
    return render_template('visualization/clustergrammer/kegg_overlap.html')


@ui_blueprint.route('/reactome_overlap', methods=['GET'])
def reactome_matrix():
    """Renders the Reactome Matrix page powered by Clustergrammer"""
    return render_template('visualization/clustergrammer/reactome_overlap.html')


@ui_blueprint.route('/wikipathways_overlap', methods=['GET'])
def wikipathways_matrix():
    """Renders the WikiPathways Matrix page powered by Clustergrammer"""
    return render_template('visualization/clustergrammer/wikipathways_overlap.html')
