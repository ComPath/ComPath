# -*- coding: utf-8 -*-

"""This module contains the curation views in ComPath."""

import logging
from io import StringIO, BytesIO

from flask import (
    abort,
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for
)
from flask_security import current_user, login_required, roles_required

from compath.constants import BLACK_LIST, EQUIVALENT_TO, IS_PART_OF, MAPPING_TYPES
from compath.utils import (
    get_mappings,
    get_most_similar_names,
    get_pathway_model_by_name,
    to_csv
)

log = logging.getLogger(__name__)
curation_blueprint = Blueprint('curation', __name__)

"""Curation views"""


@curation_blueprint.route('/curate')
@login_required
def create_mapping():
    """Render the curation page."""
    return render_template(
        'curation/create_mapping.html',
        manager_names=current_app.manager_dict.keys(),
        BLACK_LIST=BLACK_LIST
    )


@curation_blueprint.route('/mapping_catalog')
def catalog():
    """Render the mapping catalog page."""
    if request.args.get(EQUIVALENT_TO):
        mappings = current_app.manager.get_mappings_by_type(EQUIVALENT_TO)
        flash('You are visualizing the catalog of equivalent mappings')

    elif request.args.get(IS_PART_OF):
        mappings = current_app.manager.get_mappings_by_type(IS_PART_OF)
        flash('You are visualizing the catalog of hierarhical mappings')

    else:
        mappings = current_app.manager.get_all_mappings()

    return render_template(
        'curation/catalog.html',
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
    mappings = get_mappings(current_app.manager, only_accepted=False if request.args.get('all') else True)

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
    """Processes the vote.

    :param int mapping_id: id of the mapping to process the vote info
    :param int type: 0 if down vote and 1 if up vote
    """
    if type not in {0, 1}:
        return abort(500, "Invalid vote type {}. Vote type should be 0 or 1".format(type))

    mapping = current_app.manager.get_mapping_by_id(mapping_id)

    if mapping is None:
        return abort(404, "Missing mapping for ID {}".format(mapping_id))

    vote = current_app.manager.get_or_create_vote(current_user, mapping, vote_type=(type == 1))

    # Accept mapping if there are enough votes
    if not vote.mapping.accepted and vote.mapping.is_acceptable:
        vote.mapping.accepted = True
        current_app.manager.session.add(vote)
        current_app.manager.session.commit()

        flash("The mapping you just voted had enough number of votes to be accepted")

    return redirect(url_for('.catalog'))


@curation_blueprint.route('/mapping/<int:mapping_id>/accept')
@roles_required('admin')
def accept_mapping(mapping_id):
    """Process a vote.

    :param int mapping_id: id of the mapping to be accepted by the admin
    """
    mapping, created = current_app.manager.accept_mapping(mapping_id)

    if not mapping:
        return abort(404, "Missing mapping for ID {}".format(mapping_id))

    if created is False:
        flash("The mapping was already accepted")

    flash("You have accepted the mapping between {} and {}".format(
        mapping.service_1_pathway_name,
        mapping.service_2_pathway_name)
    )

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
        flash("Missing or incorrect mapping type", category='warning')
        return redirect(url_for('.create_mapping'))

    resource_1 = request.args.get('resource-1')
    if not resource_1:
        flash("Invalid request. Missing 'resource-1' arguments in the request", category='warning')
        return redirect(url_for('.create_mapping'))
    if resource_1 not in current_app.manager_dict:
        flash("'{}' does not exist or has not been loaded in ComPath".format(resource_1), category='warning')
        return redirect(url_for('.create_mapping'))

    resource_2 = request.args.get('resource-2')
    if not resource_2:
        flash("Invalid request. Missing 'resource-2' arguments in the request", category='warning')
        return redirect(url_for('.create_mapping'))

    if resource_2 not in current_app.manager_dict:
        flash("'{}' does not exist or has not been loaded in ComPath".format(resource_2), category='warning')
        return redirect(url_for('.create_mapping'))

    pathway_1 = request.args.get('pathway-1')
    if not pathway_1:
        flash("Missing pathway 1", category='warning')
        return redirect(url_for('.create_mapping'))

    pathway_2 = request.args.get('pathway-2')
    if not pathway_2:
        flash("Missing pathway 2", category='warning')
        return redirect(url_for('.create_mapping'))

    pathway_1_model = get_pathway_model_by_name(current_app.manager_dict, resource_1, pathway_1)
    pathway_2_model = get_pathway_model_by_name(current_app.manager_dict, resource_2, pathway_2)

    if pathway_1_model == pathway_2_model:
        flash("Trying to establish a mapping between the same pathway")
        return redirect(url_for('.create_mapping'))

    if pathway_1_model is None:
        return abort(500, "Pathway 1 '{}' not found in manager '{}'".format(pathway_1, resource_1))

    if pathway_2_model is None:
        return abort(500, "Pathway 2 '{}' not found in manager '{}'".format(pathway_2, resource_2))

    mapping, created = current_app.manager.get_or_create_mapping(
        resource_1,
        getattr(pathway_1_model, '{}_id'.format(resource_1)),
        pathway_1_model.name,
        resource_2,
        getattr(pathway_2_model, '{}_id'.format(resource_2)),
        pathway_2_model.name,
        mapping_type,
        current_user
    )

    if not created:
        claimed = current_app.manager.claim_mapping(mapping, current_user)
        if not claimed:
            flash("You already established this mapping", category='warning')
        else:
            flash("Since this mapping was already established, you have been assigned as a creator of the mapping")
    else:
        flash("You have established a new mapping between {} and {} with the mapping type {}".format(
            pathway_1_model.name,
            pathway_2_model.name,
            mapping_type)
        )

    return render_template(
        'curation/create_mapping.html',
        manager_names=current_app.manager_dict.keys(),
    )


@curation_blueprint.route('/suggest_mappings/name/<pathway_name>')
def suggest_mappings_by_name(pathway_name):
    """Return list of top matches based on string similarity.

    :param str pathway_name:
    """
    # Get all pathway names from each resource
    pathways_dict = {
        manager: external_manager.get_all_pathway_names()
        for manager, external_manager in current_app.manager_dict.items()
        if manager not in BLACK_LIST
    }

    # Flat list of lists
    pathways_lists = [pathway for pathway_list in pathways_dict.values() for pathway in pathway_list]

    # TODO: Do this dynamically
    # Remove suffix from KEGG
    pathways_lists = map(lambda x: str.replace(x, " - Homo sapiens (human)", ""), pathways_lists)

    top_pathways = {
        pathway_name
        for pathway_name, value in get_most_similar_names(pathway_name, pathways_lists)
    }

    results = []

    for pathway in top_pathways:
        # Find to which manager the pathway belongs to and get identifier
        for manager, pathways in pathways_dict.items():

            if pathway in pathways:
                results.append(
                    [
                        manager,
                        current_app.manager_dict[manager].get_pathway_by_name(pathway).resource_id,
                        pathway
                    ]
                )

    # Return the top 5 most similar ones
    return jsonify(results)
