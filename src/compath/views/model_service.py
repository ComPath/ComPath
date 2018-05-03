# -*- coding: utf-8 -*-

"""This module contains the common views across all pathway bio2bel repos."""

import logging

from compath.constants import EQUIVALENT_TO, IS_PART_OF
from compath.models import PathwayMapping, Vote
from compath.utils import get_pathway_model_by_id

from flask import (
    abort,
    Blueprint,
    current_app,
    render_template
)

from flask_admin.contrib.sqla import ModelView

log = logging.getLogger(__name__)
model_blueprint = Blueprint('model', __name__)

"""Admin views"""


class MappingView(ModelView):
    """Mapping view in Flask-admin."""
    column_searchable_list = (
        PathwayMapping.service_1_name,
        PathwayMapping.service_1_pathway_id,
        PathwayMapping.service_1_pathway_name,
        PathwayMapping.type,
        PathwayMapping.service_2_name,
        PathwayMapping.service_2_pathway_id,
        PathwayMapping.service_2_pathway_name,
    )
    column_list = (
        PathwayMapping.service_1_name,
        PathwayMapping.service_1_pathway_id,
        PathwayMapping.service_1_pathway_name,
        PathwayMapping.type,
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


@model_blueprint.route('/pathway/<resource>/<identifier>')
def pathway_view(resource, identifier):
    """Render the pathway view page."""

    if resource not in current_app.manager_dict:
        abort(404, "'{}' does not exist or has not been loaded in ComPath".format(resource))

    pathway = get_pathway_model_by_id(current_app, resource, identifier)

    if not pathway:
        abort(404, 'Pathway not found for identifier "{}"'.format(identifier))

    mappings = current_app.manager.get_all_mappings_from_pathway(resource, identifier, pathway.name)

    super_pathways = []

    sub_pathways = []

    equivalent_pathways = []

    for mapping in mappings:

        if mapping.type == EQUIVALENT_TO:
            if mapping.service_1_pathway_id == pathway.resource_id:
                equivalent_pathways.append(
                    (
                        mapping.service_2_name,
                        mapping.service_2_pathway_id,
                        mapping.service_2_pathway_name
                    )

                )

            else:
                equivalent_pathways.append(
                    (
                        mapping.service_1_name,
                        mapping.service_1_pathway_id,
                        mapping.service_1_pathway_name
                    )
                )

        elif mapping.type == IS_PART_OF:
            if mapping.service_1_pathway_id == pathway.resource_id:
                super_pathways.append(
                    (
                        mapping.service_2_name,
                        mapping.service_2_pathway_id,
                        mapping.service_2_pathway_name
                    )

                )

            else:
                sub_pathways.append(
                    (
                        mapping.service_1_name,
                        mapping.service_1_pathway_id,
                        mapping.service_1_pathway_name
                    )
                )
        else:
            raise ValueError('Error with mapping type')

    return render_template(
        'models/pathway.html',
        pathway=pathway,
        resource=resource,
        equivalent_pathways=equivalent_pathways,
        sub_pathways=sub_pathways,
        super_pathways=super_pathways
    )
