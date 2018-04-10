# -*- coding: utf-8 -*-

""" This module contains the common views across all pathway bio2bel repos"""

import logging

from flask import (
    Blueprint,
    render_template,
    current_app,
    abort
)
from flask_admin.contrib.sqla import ModelView

from compath.models import PathwayMapping, Vote
from compath.utils import get_pathway_model_by_id

log = logging.getLogger(__name__)
model_blueprint = Blueprint('model', __name__)

"""Admin views"""


class MappingView(ModelView):
    """Mapping view in Flask-admin"""

    column_list = (
        PathwayMapping.service_1_name,
        PathwayMapping.service_1_pathway_id,
        PathwayMapping.service_1_pathway_name,
        PathwayMapping.service_2_name,
        PathwayMapping.service_2_pathway_id,
        PathwayMapping.service_2_pathway_name,
        'accepted',
        'count_creators',
        'count_up_votes',
        'count_down_votes',
    )


class VoteView(ModelView):
    """Vote view in Flask-admin"""
    column_searchable_list = (
        Vote.mapping_id,
        Vote.changed,
        Vote.type,
    )

    column_display_all_relations = [
        Vote.user,
        Vote.mapping
    ]


"""Model views"""


@model_blueprint.route('/pathway/<resource>/<identifier>', methods=['GET'])
def pathway_view(resource, identifier):
    pathway = get_pathway_model_by_id(current_app, resource, identifier)

    if not pathway:
        abort(404, 'Pathway not found')

    return render_template('models/pathway.html', pathway=pathway, resource=resource)
