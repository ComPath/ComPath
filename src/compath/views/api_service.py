# -*- coding: utf-8 -*-

"""This module contains the API views in ComPath."""

import logging

from flask import (Blueprint, current_app, jsonify, request)

from compath.constants import BLACK_LIST
from compath.utils import (
    get_gene_pathways
)

log = logging.getLogger(__name__)
api_blueprint = Blueprint('api', __name__)

"""Gene Autocompletion and Query"""


@api_blueprint.route('/api/get_pathways_by_gene/<hgnc_symbol>')
def api_get_gene_pathways(hgnc_symbol):
    """Query the pathways associated with a gene.

    :param str hgnc_symbol: gene symbol
    """
    pathways = get_gene_pathways(current_app.manager_dict, hgnc_symbol)

    if all(value is None for value in pathways.values()):
        return jsonify({})

    return jsonify(pathways)


@api_blueprint.route('/api/autocompletion/gene_symbol')
def api_gene_autocompletion_all_resources():
    """Autocompletion for gene symbol."""
    q = request.args.get('q')

    # Return empty json if no request in the argument
    if not q:
        return jsonify([])

    hgnc_symbols = set()

    for manager_name, manager in current_app.manager_dict.items():
        if manager_name in BLACK_LIST:
            continue

        genes = manager.query_similar_hgnc_symbol(q)

        if not genes:
            continue

        for gene in genes:
            hgnc_symbols.add(gene.hgnc_symbol)

    # Return empty json if no genes matching in the DB
    if not hgnc_symbols:
        return jsonify([])

    return jsonify(list(hgnc_symbols))


"""Pathway Autocompletion and Query"""


@api_blueprint.route('/api/autocompletion/pathway_name')
def api_pathway_autocompletion_resource_specific():
    """Autocompletion for pathway name given a database."""
    q = request.args.get('q')
    resource = request.args.get('resource')

    if not q or not resource:
        return jsonify([])

    resource = resource.lower()

    manager = current_app.manager_dict.get(resource)

    if not manager:
        return jsonify([])

    # Special method for ComPath HGNC since it does not have a pathway model but gene families
    if resource == 'compath_hgnc':
        return jsonify(manager.autocomplete_gene_families(q, 10))

    return jsonify(list({
        pathway.name
        for pathway in manager.query_pathway_by_name(q, 10)  # Limits the results returned to 10
        if pathway
    }))


@api_blueprint.route('/api/autocompletion/pathway/<name>')
def api_pathway_autocompletion_all_resources(name):
    """Pathway name autocompletion, looking at all databases/plugins installed.

    :param str name: pathway name to search
    """
    similar_pathways = {}

    for resource_name, ExternalManager in current_app.manager_dict.items():
        if resource_name in BLACK_LIST:
            continue

        similar_pathways[resource_name] = ExternalManager.query_similar_pathways(name, top=5)

    similar_pathways = [
        (resource_name, pathway_id, pathway_name)
        for resource_name, pathways in similar_pathways.items()
        for pathway_name, pathway_id in pathways
    ]

    return jsonify(similar_pathways)
