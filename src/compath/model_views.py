# -*- coding: utf-8 -*-

""" This module contains the common views across all pathway bio2bel repos"""

import logging

from flask import (
    Blueprint,
    render_template,
    current_app
)

from .utils import (
    get_pathway_model_by_id
)

log = logging.getLogger(__name__)
model_blueprint = Blueprint('model', __name__)

"""Model views"""


@model_blueprint.route('/pathway/<resource>/<identifier>', methods=['GET'])
def pathway_view(resource, identifier):
    pathway = get_pathway_model_by_id(current_app, resource, identifier)

    return render_template('models/pathway.html', pathway=pathway, resource=resource)
