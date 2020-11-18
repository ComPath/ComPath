# -*- coding: utf-8 -*-

"""This module contains the API views in ComPath."""

import logging

from flask import Blueprint, abort, jsonify, request

from ..constants import BLACKLIST
from ..state import bio2bel_managers
from ..utils import get_gene_pathways

logger = logging.getLogger(__name__)

api_blueprint = Blueprint('api', __name__)


@api_blueprint.route('/api/installed_plugins')
def installed_plugins():
    """Return the installed plugins."""
    _installed_plugins = list(bio2bel_managers)

    if not _installed_plugins:
        abort(500, 'There are no plugins installed')

    return jsonify(_installed_plugins)


@api_blueprint.route('/api/plugins_populated')
def plugins_populated():
    """Check if all plugins are populated."""
    installed_plugins = {
        resource_name: manager.is_populated()
        for resource_name, manager in bio2bel_managers.items()
    }

    if all(installed_plugins.values()):
        return jsonify(installed_plugins)

    return abort(500, 'Not all plugins are populated')


"""Gene Autocompletion and Query"""


@api_blueprint.route('/api/get_pathways_by_gene/<hgnc_symbol>')
def api_get_gene_pathways(hgnc_symbol):
    """Query the pathways associated with a gene.
       ---
       tags:
         - miscellaneous
       parameters:
         - name: hgnc_symbol
           type: string
           description: gene symbol
           required: true
           x-example: APP
       responses:
         200:
           description: pathway dict in JSON.
    """
    pathways = get_gene_pathways(bio2bel_managers, hgnc_symbol)

    if all(value is None for value in pathways.values()):
        return jsonify({})

    return jsonify(pathways)


@api_blueprint.route('/api/autocompletion/gene_symbol')
def api_gene_autocompletion_all_resources():
    """Autocompletion for gene symbol.
        ---
        tags:
          - autocompletion
        responses:
          200:
            description: list of all hgnc_symbols in JSON for the autocompletion.
     """
    q = request.args.get('q')

    # Return empty json if no request in the argument
    if not q:
        return jsonify([])

    return jsonify(list({
        gene.hgnc_symbol
        for manager_name, manager in bio2bel_managers.items()
        if manager_name not in BLACKLIST
        for gene in manager.search_genes(q)
    }))


"""Pathway Autocompletion and Query"""


@api_blueprint.route('/api/autocompletion/pathway_name')
def api_pathway_autocompletion_resource_specific():
    """Autocompletion for pathway name given a database.
        ---
        tags:
          - autocompletion
        responses:
          200:
            description: returns a list for the autocompletion of 10 pathway in JSON.
     """
    q = request.args.get('q')
    resource = request.args.get('resource')

    if not q or not resource:
        return jsonify([])

    resource = resource.lower()

    manager = bio2bel_managers.get(resource)

    if not manager:
        return jsonify([])

    # Special method for ComPath HGNC since it does not have a pathway model but gene families
    if resource == 'compath_hgnc':
        return jsonify(manager.autocomplete_gene_families(q, limit=10))

    return jsonify(list({
        pathway.name
        for pathway in manager.search_pathways(q, limit=10)  # Limits the results returned to 10
    }))


@api_blueprint.route('/api/autocompletion/pathway/<name>')
def api_pathway_autocompletion_all_resources(name: str):
    """Pathway name autocompletion, looking at all databases/plugins installed.
       ---
       tags:
         - autocompletion
       parameters:
         - name: name
           type: string
           x-example: 'AKT1'
           description: pathway name to search
       responses:
         200:
           description: returns a list for the autocompletion of 10 pathway in JSON.

     """
    return jsonify([
        (prefix, pathway.identifier, pathway.name)
        for prefix, manager in bio2bel_managers.items()
        if prefix not in BLACKLIST
        for pathway in manager.search_pathways(name, limit=5)
    ])
