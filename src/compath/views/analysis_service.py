# -*- coding: utf-8 -*-

"""This module contains the analysis views in ComPath."""

import itertools as itt
import logging
from io import StringIO

from flask import Blueprint, abort, current_app, flash, jsonify, make_response, redirect, render_template, request

from ..constants import BLACKLIST, STYLED_NAMES
from ..forms import GeneSetFileForm, GeneSetForm
from ..state import bio2bel_managers, compath_state, web_manager
from ..utils import (
    dict_to_pandas_df, get_enriched_pathways, get_genes_without_assigned_pathways, get_pathway_model_by_name,
    perform_hypergeometric_test, process_form_gene_set, process_overlap_for_venn_diagram,
)
from ..visualization.cytoscape import (
    enrich_graph_with_mappings, filter_network_by_similarity, networkx_to_cytoscape_js, pathways_to_similarity_network,
)
from ..visualization.d3_dendrogram import get_dendrogram_tree

logger = logging.getLogger(__name__)

analysis_blueprint = Blueprint('analysis', __name__)

"""Cytoscape view"""


@analysis_blueprint.route('/similarity_network')
def similarity_network():
    """Render the Similarity network powered by Cytoscape."""
    return render_template(
        'visualization/similarity_network.html',
        manager_names=bio2bel_managers.keys(),
    )


"""Simulation view"""


@analysis_blueprint.route('/simulation')
def simulation_view():
    """Return the Simulation page"""
    return render_template(
        'visualization/simulation.html',
        results=compath_state.simulation_results,
    )


"""Venn Diagram views"""


@analysis_blueprint.route('/query/overlap')
def calculate_overlap():
    """Return the overlap between different pathways in order to generate a Venn diagram.
       ---
       tags:
         - miscellaneous
       responses:
         200:
           description: processed venn diagram.
    """
    pathways_list = request.args.getlist('pathways[]')
    resources_list = request.args.getlist('resources[]')

    pathways = list(zip(pathways_list, resources_list))

    if len(pathways) < 2:
        return abort(500, 'Only one set given')

    gene_sets, pathway_manager_dict = get_gene_sets_from_pathway_names(pathways)

    # Get URLs to original pathways so it can be displayed in the info table
    pathway_name_to_original = {}
    pathway_name_to_mappings = {}
    for pathway_name, resource in pathway_manager_dict.items():
        pathway = get_pathway_model_by_name(bio2bel_managers, resource, pathway_name)

        if not pathway or not pathway.url:
            continue

        pathway_name_to_mappings[pathway_name] = 'https://compath.scai.fraunhofer.de/pathway/{}/{}'.format(
            resource,
            pathway.resource_id
        )
        pathway_name_to_original[pathway_name] = pathway.url

    if len(gene_sets) < 2:
        return abort(500, 'Only one valid set given')

    processed_venn_diagram = process_overlap_for_venn_diagram(gene_sets)

    return jsonify(processed_venn_diagram, pathway_name_to_original, pathway_name_to_mappings)


@analysis_blueprint.route('/pathway_overlap')
def pathway_overlap():
    """Render the Pathway Overlap page."""
    return render_template(
        'visualization/venn_diagram/venn_diagram_view.html',
        manager_names=bio2bel_managers.keys(),
        BLACK_LIST=BLACKLIST,
        STYLED_NAMES=STYLED_NAMES,
    )


"""Histogram view"""


@analysis_blueprint.route('/database_distributions/<resource>')
def database_distributions(resource: str):
    """Render the Pathway Database distributions.

    :param resource: name of the pathway database to visualize its distribution
    """
    if (
        resource not in compath_state.resource_to_pathway_distribution
        or resource not in compath_state.resource_to_gene_distribution
    ):
        return abort(500, 'Invalid request. Not a valid manager')

    return render_template(
        'visualization/database_distributions.html',
        pathway_data=compath_state.resource_to_pathway_distribution[resource],
        gene_data=compath_state.resource_to_gene_distribution[resource],
        resource=resource,
        STYLED_NAMES=STYLED_NAMES,
    )


"""Query submission handling views"""


@analysis_blueprint.route('/query')
def query():
    """Return the Query page"""
    text_form = GeneSetForm()
    file_form = GeneSetFileForm()
    return render_template(
        'query.html',
        text_form=text_form,
        file_form=file_form,
    )


@analysis_blueprint.route('/query/results', methods=['POST'])
def process_gene_set():
    """Process the gene set POST form."""
    text_form = GeneSetForm()
    file_form = GeneSetFileForm()

    if text_form.validate_on_submit():
        gene_sets = process_form_gene_set(text_form.geneset.data)
        filter_by_significance = text_form.filter_non_significant.data

    elif file_form.validate_on_submit():
        gene_sets = process_form_gene_set(file_form.file.data.stream.read().decode("utf-8"))
        filter_by_significance = False  # TODO: Enable it from file too

    else:
        flash('The submitted gene set is not valid')
        return redirect('/query')

    enrichment_results = get_enriched_pathways(bio2bel_managers, gene_sets)

    # Ensures that submitted genes are in HGNC Manager
    valid_gene_sets = current_app.gene_universe.intersection(gene_sets)

    if not valid_gene_sets:
        flash('ComPath could not find any valid HGNC Symbol from the submitted list.')

    elif not any(enrichment_results.values()):
        flash('The Gene Symbols submitted do not match to any pathway.')

    else:
        enrichment_results = perform_hypergeometric_test(
            valid_gene_sets,
            enrichment_results,
            len(current_app.gene_universe),
            filter_by_significance,
        )

    return render_template(
        'visualization/enrichment_results.html',
        query_results=enrichment_results,
        submitted_gene_set=valid_gene_sets,
        number_of_pathways=len(list(itt.chain(*enrichment_results.values()))),
        genes_not_in_pathways=get_genes_without_assigned_pathways(enrichment_results, valid_gene_sets),
        STYLED_NAMES=STYLED_NAMES,
    )


@analysis_blueprint.route('/compare_pathways')
def compare_pathways():
    """Render a visualization comparing pathways."""
    if not any(arg in request.args for arg in ("analysis", "pathways[]")):
        return abort(500, 'Invalid request. Missing analysis or pathways[] arguments in the request')

    analysis_type = request.args["analysis"]

    pathways = [
        (pathway.split('|')[1], pathway.split('|')[0])
        for pathway in request.args.getlist('pathways[]')
    ]

    if len(pathways) <= 1:
        return abort(500, 'At least two pathways should be sent as arguments.')

    # Gene sets as well as pathway->manager name dictionary
    gene_sets, pathway_manager_dict = get_gene_sets_from_pathway_names(pathways)

    if not gene_sets:
        return abort(
            500,
            'Pathways could not be found. '
            'Please make sure you have submitted a correct request or contact the administrator',
        )

    if analysis_type == 'venn':
        # Process the overlap and send the json needed for venn diagram view
        processed_venn_diagram = process_overlap_for_venn_diagram(gene_sets)

        return render_template(
            'visualization/venn_diagram/pathway_overlap.html',
            venn_diagram_data=processed_venn_diagram,
        )

    elif analysis_type == 'dendrogram':
        # Calculate dendrogram and send it to the view
        tree_json, number_of_pathways = get_dendrogram_tree(gene_sets, pathway_manager_dict)

        return render_template(
            'visualization/dendrogram/dendrogram.html',
            tree_json=tree_json,
            numberNodes=number_of_pathways,
        )

    elif analysis_type == 'network':

        # Get pathways triplet info to get their mappings in ComPath
        pathway_info = get_pathway_info(pathways)

        similarity_graph = pathways_to_similarity_network(bio2bel_managers, pathway_info)

        if 'mappings' in request.args:
            # Get the mappings corresponding to each pathway queried
            mappings = [
                web_manager.get_all_mappings_from_pathway(resource, pathway_id, pathway_name)
                for resource, pathway_id, pathway_name in pathway_info
            ]

            mappings = [item for sublist in mappings for item in sublist]  # Flat list of lists

            enrich_graph_with_mappings(similarity_graph, mappings)

        similarity_filter = request.args.get('filter', type=float)
        if similarity_filter is not None:
            filter_network_by_similarity(similarity_graph, similarity_filter)

        cytoscape_graph = networkx_to_cytoscape_js(similarity_graph)

        return render_template(
            'visualization/pathway_neighbourhood.html',
            cytoscape_graph=cytoscape_graph
        )

    else:
        return abort(500, 'Not a valid analysis method')


"""Export views"""


@analysis_blueprint.route('/export/<resource>')
def export_gene_set(resource):
    """Export gene set to excel.
       ---
       tags:
         - miscellaneous
       parameters:
         - name: resource
           type: string
           description: name of the pathway database to visualize its distribution
           required: true
           x-example: KEGG
       responses:
         200:
           description: csv output file of the gene set.
    """
    resource_manager = bio2bel_managers.get(resource)

    if not resource_manager:
        return abort(404, '{} resource not found'.format(resource))

    logger.info("Querying the database")

    genesets = dict_to_pandas_df(resource_manager.get_pathway_name_to_hgnc_symbols())
    sio = StringIO()

    genesets.to_csv(sio)

    output = make_response(sio.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename={}_gene_sets.csv".format(resource)
    output.headers["Content-type"] = "text/csv"
    return output


def get_gene_sets_from_pathway_names(pathways):
    """Return the gene sets for a given pathway/resource tuple.

    :param list[tuple[str,str] pathways: pathway/resource tuples
    :rtype: tuple[dict[str,set[str]],dict[str,str]]
    :return: gene sets
    """
    gene_sets = {}

    pathway_manager_dict = {}

    for name, resource in pathways:

        pathway = get_pathway_model_by_name(bio2bel_managers, resource, name)

        if not pathway:
            logger.warning('{} pathway not found'.format(name))
            continue

        # Ensure no duplicates are passed
        if name in gene_sets:
            name = "{}_{}".format(name, resource)

        # Check if pathway has no genes
        if not pathway.proteins:
            continue

        pathway_manager_dict[name] = resource

        gene_sets[name] = {
            protein.hgnc_symbol
            for protein in pathway.proteins
        }

    return gene_sets, pathway_manager_dict


def get_pathway_info(pathways):
    """Return the gene sets for a given pathway/resource tuple.

    :param flask.Flask app: current app
    :param list[tuple[str,str] pathways: pathway/resource tuples
    :rtype: list
    :return: pathway info
    """
    pathway_info = []

    for name, resource in pathways:

        pathway = get_pathway_model_by_name(bio2bel_managers, resource, name)

        if not pathway:
            logger.warning('%s pathway not found', name)
            continue

        pathway_info.append((resource, pathway.resource_id, pathway.name))

    return pathway_info
