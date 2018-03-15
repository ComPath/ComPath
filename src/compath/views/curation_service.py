# -*- coding: utf-8 -*-

""" This module contains the curation views in ComPath"""

import logging

from flask import (
    Blueprint,
    render_template,
    flash,
    current_app,
    request,
    abort,
    redirect,
    url_for
)
from flask_security import current_user, login_required

from compath.utils import (
    get_pathway_model_by_name
)

log = logging.getLogger(__name__)
curation_blueprint = Blueprint('curation', __name__)

"""Curation views"""


@curation_blueprint.route('/curation', methods=['GET'])
@login_required
def curation():
    """Renders the curation page"""
    return render_template(
        'curation/create_mapping.html',
        manager_names=current_app.manager_dict.keys(),
    )


@curation_blueprint.route('/mapping_catalog', methods=['GET'])
def catalog():
    """Renders the mapping catalog page"""

    return render_template(
        'curation/catalog.html',
        mappings=current_app.manager.get_mappings()
    )


@curation_blueprint.route('/vote/<int:mapping_id>/<int:type>', methods=['GET', 'POST'])
@login_required
def process_vote(mapping_id, type):
    """Processes the vote

    :param int mapping_id: id of the mapping to process the vote info
    :param int type: 0 if down vote and 1 if up vote
    """

    if type not in {0, 1}:
        return abort(500, "Invalid vote type {}. Vote type should be 0 or 1".format(type))

    mapping = current_app.manager.get_mapping_by_id(mapping_id)

    if mapping is None:
        return abort(404, "Missing mapping for ID {}".format(mapping_id))

    vote = current_app.manager.get_or_create_vote(current_user, mapping, vote_type=(type == 1))

    return redirect(url_for('.catalog'))


@curation_blueprint.route('/map_pathways', methods=['GET', 'POST'])
@login_required
def process_mapping():
    """Processes the mapping between two pathways"""

    resource_1 = request.args.get('resource-1')

    if resource_1 is None:
        return abort(500, "Invalid request. Missing 'resource-1' arguments in the request")

    if resource_1 not in current_app.manager_dict:
        return abort(500, "'{}' does not exist or has not been loaded in ComPath".format(resource_1))

    resource_2 = request.args.get('resource-2')

    if resource_2 is None:
        return abort(500, "Invalid request. Missing 'resource-2' arguments in the request")

    if resource_2 not in current_app.manager_dict:
        return abort(500, "'{}' does not exist or has not been loaded in ComPath".format(resource_2))

    pathway_1 = request.args.get('pathway-1')
    pathway_2 = request.args.get('pathway-2')

    pathway_1_model = get_pathway_model_by_name(current_app, resource_1, pathway_1)
    pathway_2_model = get_pathway_model_by_name(current_app, resource_2, pathway_2)

    if pathway_1 == pathway_2:
        flash("Trying to establish a mapping between the same pathway")
        return render_template(
            'curation/create_mapping.html',
            manager_names=current_app.manager_dict.keys(),
        )

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
        current_user
    )

    if created is False:

        if current_user in mapping.creators:
            flash("You already established this mapping")
        else:
            flash("Since this mapping was already established, you have been assigned as a creator of the mapping")
            current_app.manager.claim_mapping(mapping, current_user)

    else:
        flash("You have established a new mapping between {} and {}".format(pathway_1_model.name, pathway_2_model.name))

    return render_template(
        'curation/create_mapping.html',
        manager_names=current_app.manager_dict.keys(),
    )
