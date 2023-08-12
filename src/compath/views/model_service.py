# -*- coding: utf-8 -*-

"""This module contains the common views across all pathway bio2bel repos."""

import logging

from flask import (Blueprint, abort, render_template, request)
from flask_admin.contrib.sqla import ModelView

from .utils import get_pathway_model_by_id
from ..constants import EQUIVALENT_TO, IS_PART_OF, STYLED_NAMES
from ..models import PathwayMapping, Vote
from ..state import bio2bel_managers, web_manager
from ..visualization.d3_dendrogram import get_mapping_dendrogram

logger = logging.getLogger(__name__)

model_blueprint = Blueprint('model', __name__)


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
        Vote.mapping,
    ]


"""Model views"""


@model_blueprint.route('/pathway/<prefix>/<identifier>')
def pathway_view(prefix: str, identifier: str):
    """Render the pathway view page."""
    if prefix not in bio2bel_managers:
        abort(404, f"'{prefix}' does not exist or has not been loaded in ComPath")

    pathway = get_pathway_model_by_id(prefix, identifier)

    if not pathway:
        abort(404, f'Pathway not found for identifier {prefix}:{identifier}')

    mappings = web_manager.get_all_mappings_from_pathway(prefix, identifier, pathway.name)

    super_pathways = []

    sub_pathways = []

    equivalent_pathways = []

    for mapping in mappings:
        if mapping.type == EQUIVALENT_TO:
            if mapping.service_1_pathway_id == pathway.identifier:
                equivalent_pathways.append((
                    mapping.service_2_name,
                    mapping.service_2_pathway_id,
                    mapping.service_2_pathway_name,
                ))
            else:
                equivalent_pathways.append((
                    mapping.service_1_name,
                    mapping.service_1_pathway_id,
                    mapping.service_1_pathway_name,
                ))
        elif mapping.type == IS_PART_OF:
            if mapping.service_1_pathway_id == pathway.identifier:
                super_pathways.append((
                    mapping.service_2_name,
                    mapping.service_2_pathway_id,
                    mapping.service_2_pathway_name,
                ))

            else:
                sub_pathways.append((
                    mapping.service_1_name,
                    mapping.service_1_pathway_id,
                    mapping.service_1_pathway_name,
                ))
        else:
            raise ValueError(f'Unexpected mapping type: {mapping.type}')

    d3_tree = get_mapping_dendrogram(web_manager, prefix, identifier, pathway.name)

    return render_template(
        'models/pathway.html',
        pathway=pathway,
        equivalent_pathways=equivalent_pathways,
        sub_pathways=sub_pathways,
        super_pathways=super_pathways,
        submitted_gene_set=request.args.get('gene_set'),
        STYLED_NAMES=STYLED_NAMES,
        dendrogram=[] if not d3_tree['children'] else d3_tree
    )
