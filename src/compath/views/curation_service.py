# -*- coding: utf-8 -*-

"""This module contains the curation views in ComPath."""

import logging
from collections import Mapping, defaultdict
from io import BytesIO, StringIO
from typing import List, Tuple

from flask import Blueprint, Markup, abort, flash, jsonify, redirect, render_template, request, send_file, url_for
from flask_security import current_user, login_required, roles_required

from .utils import get_pathway_model_by_id
from ..constants import BLACKLIST, EQUIVALENT_TO, IS_PART_OF, MAPPING_TYPES, STYLED_NAMES
from ..state import bio2bel_managers, web_manager
from ..utils import (
    calculate_szymkiewicz_simpson_coefficient, get_most_similar_names, get_pathway_model_by_name, get_top_matches,
    to_csv,
)

logger = logging.getLogger(__name__)

curation_blueprint = Blueprint('curation', __name__)


@curation_blueprint.route('/curate')
@login_required
def create_mapping():
    """Render the curation page."""
    return render_template(
        'curation/create_mapping.html',
        manager_names=bio2bel_managers.keys(),
        BLACK_LIST=BLACKLIST,
        STYLED_NAMES=STYLED_NAMES
    )


@curation_blueprint.route('/catalog')
def catalog():
    """Render the mapping catalog page."""
    if request.args.get(EQUIVALENT_TO):
        mappings = web_manager.get_mappings_by_type(EQUIVALENT_TO)
        message = Markup("<h4>You are now visualizing the catalog of equivalent mappings</h4>")
        flash(message)

    elif request.args.get(IS_PART_OF):
        mappings = web_manager.get_mappings_by_type(IS_PART_OF)
        message = Markup("<h4>You are now visualizing the catalog of hierarchical mappings</h4>")
        flash(message)

    else:
        mappings = web_manager.get_all_mappings()

    return render_template(
        'curation/catalog.html',
        STYLED_NAMES=STYLED_NAMES,
        mappings=mappings,
        all='all'
    )


@curation_blueprint.route('/export_mappings')
def export_mappings():
    """Export mappings.
    ---
    tags:
      - mappings
    parameters:
      - name: all
        type: string
        required: false
    responses:
      200:
        description: A tsv file with mappings
    """
    mappings = _get_mappings(only_accepted=False if request.args.get('all') else True)

    string = StringIO()
    to_csv(mappings, string)
    string.seek(0)
    data = BytesIO(string.read().encode('utf-8'))
    return send_file(
        data,
        mimetype="text/tab-separated-values",
        attachment_filename="all_mappings.tsv" if request.args.get('all') else "curated_mappings.tsv",
        as_attachment=True
    )


@curation_blueprint.route('/vote/<int:mapping_id>/<int:type>')
@login_required
def process_vote(mapping_id, type):
    """Process the vote.
    ---
    tags:
      - mappings
    parameters:
      - name: mapping_id
        type: integer
        description: id of the mapping to process the vote info
        required: true

      - type: type
        type: integer
        description: 0 if down vote and 1 if up vote
        required: true

    responses:
      200:
        description: Redirects to mapping catalog
    """

    if type not in {0, 1}:
        return abort(500, f"Invalid vote type {type}. Vote type should be 0 or 1")

    mapping = web_manager.get_mapping_by_id(mapping_id)

    if mapping is None:
        return abort(404, f"Missing mapping for ID {mapping_id}")

    vote = web_manager.get_or_create_vote(current_user, mapping, vote_type=(type == 1))

    # Accept mapping if there are enough votes
    if not vote.mapping.accepted and vote.mapping.is_acceptable:
        vote.mapping.accepted = True
        web_manager.session.add(vote)
        web_manager.session.commit()

        message = Markup("<h4>The mapping you just voted had enough number of votes to be accepted</h4>")
        flash(message)

    return redirect(url_for('.catalog'))


@curation_blueprint.route('/mapping/<int:mapping_id>/accept')
@roles_required('admin')
def accept_mapping(mapping_id: int):
    """Process a vote.

    :param mapping_id: id of the mapping to be accepted by the admin
    """
    mapping, created = web_manager.accept_mapping(mapping_id)

    if not mapping:
        return abort(404, f"Missing mapping for ID {mapping_id}")

    if created is False:
        message = Markup("<h4>The mapping was already accepted</h4>")
        flash(message)

    message = Markup("<h4>You have accepted the mapping between {} ({}) and {} ({})</h4>".format(
        mapping.service_1_pathway_name,
        mapping.service_1_name,
        mapping.service_2_pathway_name,
        mapping.service_2_name,
    ))
    flash(message)

    return redirect(url_for('.catalog'))


@curation_blueprint.route('/map_pathways')
@login_required
def process_mapping():
    """Process the mapping between two pathways.

    ---
    tags:
      - mappings
    parameters:
      - name: mapping-type
        type: string
        enum: ['isPartOf', 'equivalentTo']
        required: true
      - name: resource-1
        type: string
        required: true
      - name: pathway-1
        type: string
        required: true
      - name: resource-2
        type: string
        required: true
      - name: pathway-2
        type: string
        required: true

    responses:
      200:
        description: Mapping created
    """
    mapping_type = request.args.get('mapping-type')
    if not mapping_type or mapping_type not in MAPPING_TYPES:
        message = Markup("<h4>Missing or incorrect mapping type</h4>")
        flash(message, category='warning')

        return redirect(url_for('.create_mapping'))

    resource_1 = request.args.get('resource-1')
    if not resource_1:
        message = Markup("<h4>Invalid request. Missing 'resource-1' arguments in the request</h4>")
        flash(message, category='warning')
        return redirect(url_for('.create_mapping'))

    if resource_1 not in bio2bel_managers:
        message = Markup(f"<h4>'{resource_1}' does not exist or has not been loaded in ComPath</h4>")
        flash(message, category='warning')
        return redirect(url_for('.create_mapping'))

    resource_2 = request.args.get('resource-2')
    if not resource_2:
        message = Markup("<h4>Invalid request. Missing 'resource-2' arguments in the request</h4>")
        flash(message, category='warning')
        return redirect(url_for('.create_mapping'))

    if resource_2 not in bio2bel_managers:
        message = Markup(f"<h4>'{resource_2}' does not exist or has not been loaded in ComPath</h4>")
        flash(message, category='warning')
        return redirect(url_for('.create_mapping'))

    pathway_1 = request.args.get('pathway-1')
    if not pathway_1:
        message = Markup("<h4>Missing pathway 1</h4>")
        flash(message, category='warning')
        return redirect(url_for('.create_mapping'))

    pathway_2 = request.args.get('pathway-2')
    if not pathway_2:
        message = Markup("<h4>Missing pathway 2</h4>")
        flash(message, category='warning')
        return redirect(url_for('.create_mapping'))

    pathway_1_model = get_pathway_model_by_name(bio2bel_managers, resource_1, pathway_1)
    pathway_2_model = get_pathway_model_by_name(bio2bel_managers, resource_2, pathway_2)

    if pathway_1_model is None:
        return abort(500, f"Pathway 1 '{pathway_1}' not found in manager '{resource_1}'")
    if pathway_2_model is None:
        return abort(500, f"Pathway 2 '{pathway_2}' not found in manager '{resource_2}'")
    if pathway_1_model == pathway_2_model:
        message = Markup("<h4>Trying to establish a mapping between the same pathway</h4>")
        flash(message, category='warning')
        return redirect(url_for('.create_mapping'))

    mapping, created = web_manager.get_or_create_mapping(
        resource_1,
        pathway_1_model.identifier,
        pathway_1_model.name,
        resource_2,
        pathway_2_model.identifier,
        pathway_2_model.name,
        mapping_type,
        current_user,
    )

    if not created:
        claimed = web_manager.claim_mapping(mapping, current_user)
        if not claimed:
            message = Markup("<h4>You already established this mapping</h4>")
        else:
            message = Markup(
                "<h4>Since this mapping was already established, you have been assigned as a creator of the mapping</h4>"
            )

    else:
        message = Markup(
            "<h4>You have established a new mapping between {} ({}) and {} ({}) with the mapping type {}</h4>".format(
                pathway_1_model.name,
                resource_1,
                pathway_2_model.name,
                resource_2,
                mapping_type
            ))

    flash(message)
    return redirect(url_for('.create_mapping'))


@curation_blueprint.route('/suggest_mappings/name/<pathway_name>')
def suggest_mappings_by_name(pathway_name):
    """Return list of top matches based on string similarity.
      ---
      tags:
        - mappings
      parameters:
        - name: pathway_name
          type: string
          description: textual name of the pathway
          required: true
          x-example: AKT1

      responses:
        200:
          description: The top 5 most similar pathways by name in JASON
    """
    # Get all pathway names from each resource
    pathways_dict: Mapping[str, List[Tuple[str, str]]] = {
        prefix: manager.session.query(manager.pathway_model.identifier, manager.pathway_model.name).all()
        for prefix, manager in bio2bel_managers.items()
        if prefix not in BLACKLIST
    }

    _suffix = " - Homo sapiens (human)"
    # Flat list of lists (list with all pathways in all resources)
    pathways = [
        (
            prefix,
            pathway_id,
            (
                pathway_name[:-len(_suffix)]
                if pathway_name.endswith(_suffix) else
                pathway_name
            ),
        )
        for prefix, pathways in pathways_dict.items()
        for pathway_id, pathway_name in pathways
    ]

    return jsonify(get_most_similar_names(pathway_name, pathways))


@curation_blueprint.route('/suggest_mappings/content/<resource>/<pathway_id>')
def suggest_mappings_by_content(resource, pathway_id):
    """Return list of top matches based on gene set similarity.
         ---
         tags:
           - mappings
         parameters:
           - name: resource
             type: string
             description: name of the database
             required: true
           - name: pathway_id
             type: string
             description: identifier of the pathway
             required: true
         responses:
           200:
             description: The top 5 most similar pathways by content in JASON
    """
    reference_pathway = get_pathway_model_by_id(resource, pathway_id)

    if reference_pathway is None:
        return abort(500, f"Pathway not found: {resource}:{pathway_id}")

    reference_gene_set = reference_pathway.get_hgnc_symbols()

    # Get all pathway names from each resource
    pathways_dict = {
        manager: external_manager.list_pathways()
        for manager, external_manager in bio2bel_managers.items()
        if manager not in BLACKLIST
    }

    logger.info(
        'Finding pathways similar to %s:%s ! %s',
        resource, reference_pathway.identifier, reference_pathway.name,
    )

    similar_pathways = defaultdict(list)

    for resource, pathway_list in pathways_dict.items():
        logger.info('Calculating similarities against %s', resource)
        for pathway in pathway_list:
            if len(pathway.get_hgnc_symbols()) == 0:
                continue

            similarity = calculate_szymkiewicz_simpson_coefficient(reference_gene_set, pathway.get_hgnc_symbols())
            if similarity == 0:
                continue

            similar_pathways[resource].append((resource, pathway.identifier, pathway.name, similarity))

    results = defaultdict(list)
    for resource, pathway_list in similar_pathways.items():
        results[resource].extend(get_top_matches(pathway_list, 5))
    return jsonify(dict(results))


def _get_mappings(only_accepted: bool = True):
    """Return a pandas dataframe with mappings information as an excel sheet file.

    :param only_accepted: only accepted (True) or all (False)
    """
    if only_accepted:
        mappings = web_manager.get_all_accepted_mappings()
    else:
        mappings = web_manager.get_all_mappings()

    return [
        (
            mapping.service_1_pathway_name,
            mapping.service_1_pathway_id,
            mapping.service_1_name,
            mapping.type,
            mapping.service_2_pathway_name,
            mapping.service_2_pathway_id,
            mapping.service_2_name,
        )
        for mapping in mappings
    ]
