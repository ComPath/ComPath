# -*- coding: utf-8 -*-

"""This module contains the analysis views in ComPath."""

import itertools as itt
import logging
from io import StringIO

from flask import (Blueprint, abort, current_app, flash, jsonify, make_response, redirect, render_template, request)

from compath.constants import BLACK_LIST, STYLED_NAMES
from compath.forms import GeneSetFileForm, GeneSetForm
from compath.utils import (
    dict_to_pandas_df,
    get_enriched_pathways,
    get_gene_sets_from_pathway_names,
    get_genes_without_assigned_pathways,
    get_pathway_info,
    perform_hypergeometric_test,
    process_form_gene_set
)
from compath.visualization.cytoscape import (
    enrich_graph_with_mappings,
    filter_network_by_similarity,
    networkx_to_cytoscape_js,
    pathways_to_similarity_network
)
from compath.visualization.d3_dendrogram import get_dendrogram_tree
from compath.visualization.venn_diagram import process_overlap_for_venn_diagram

log = logging.getLogger(__name__)
analysis_blueprint = Blueprint('analysis', __name__)

"""Cytoscape view"""


@analysis_blueprint.route('/similarity_network')
def similarity_network():
    """Render the Similarity network powered by Cytoscape."""
    return render_template(
        'visualization/similarity_network.html',
        manager_names=current_app.manager_dict.keys(),
    )


"""Simulation view"""


@analysis_blueprint.route('/simulation')
def simulation_view():
    """Return the Simulation page"""
    return render_template(
        'visualization/simulation.html',
        results=current_app.simulation_results,
    )


"""Venn Diagram views"""


@analysis_blueprint.route('/query/overlap')
def calculate_overlap():
    """Return the overlap between different pathways in order to generate a Venn diagram."""
    pathways_list = request.args.getlist('pathways[]')
    resources_list = request.args.getlist('resources[]')

    pathways = list(zip(pathways_list, resources_list))

    if len(pathways) < 2:
        return abort(500, 'Only one set given')

    gene_sets, pathway_manager_dict = get_gene_sets_from_pathway_names(current_app, pathways)

    if len(gene_sets) < 2:
        return abort(500, 'Only one valid set given')

    processed_venn_diagram = process_overlap_for_venn_diagram(gene_sets)

    return jsonify(processed_venn_diagram)


@analysis_blueprint.route('/pathway_overlap')
def pathway_overlap():
    """Render the Pathway Overlap page."""
    return render_template(
        'visualization/venn_diagram/venn_diagram_view.html',
        manager_names=current_app.manager_dict.keys(),
        BLACK_LIST=BLACK_LIST,
        STYLED_NAMES=STYLED_NAMES
    )


"""Histogram view"""


@analysis_blueprint.route('/database_distributions/<resource>')
def database_distributions(resource):
    """Render the Pathway Database distributions.

    :param str resource: name of the pathway database to visualize its distribution
    """
    if resource not in current_app.resource_distributions:
        return abort(500, 'Invalid request. Not a valid manager')

    return render_template(
        'visualization/database_distributions.html',
        pathway_data=current_app.resource_distributions[resource],
        gene_data=current_app.resource_distributions[resource],
        resource=resource,
        STYLED_NAMES=STYLED_NAMES
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
        file_form=file_form
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

    enrichment_results = get_enriched_pathways(current_app.manager_dict, gene_sets)

    # Ensures that submitted genes are in HGNC Manager
    valid_gene_sets = current_app.gene_universe.intersection(gene_sets)

    if valid_gene_sets:
        enrichment_results = perform_hypergeometric_test(
            valid_gene_sets,
            enrichment_results,
            len(current_app.gene_universe),
            filter_by_significance
        )
    else:
        flash('ComPath could not find any valid HGNC Symbol from the submitted list')

    return render_template(
        'visualization/enrichment_results.html',
        query_results=enrichment_results,
        submitted_gene_set=valid_gene_sets,
        number_of_pathways=len(list(itt.chain(*enrichment_results.values()))),
        genes_not_in_pathways=get_genes_without_assigned_pathways(enrichment_results, valid_gene_sets)
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
    gene_sets, pathway_manager_dict = get_gene_sets_from_pathway_names(current_app, pathways)

    if not gene_sets:
        return abort(
            500,
            'Pathways could not be found. '
            'Please make sure you have submitted a correct request or contact the administrator'
        )

    if analysis_type == 'venn':
        # Process the overlap and send the json needed for venn diagram view
        processed_venn_diagram = process_overlap_for_venn_diagram(gene_sets)

        return render_template(
            'visualization/venn_diagram/pathway_overlap.html',
            venn_diagram_data=processed_venn_diagram
        )

    elif analysis_type == 'dendrogram':
        # Calculate dendrogram and send it to the view
        tree_json, number_of_pathways = get_dendrogram_tree(gene_sets, pathway_manager_dict)

        return render_template(
            'visualization/dendrogram/dendrogram.html',
            tree_json=tree_json,
            numberNodes=number_of_pathways
        )

    elif analysis_type == 'network':

        # Get pathways triplet info to get their mappings in ComPath
        pathway_info = get_pathway_info(current_app, pathways)

        similarity_graph = pathways_to_similarity_network(current_app.manager_dict, pathway_info)

        if 'mappings' in request.args:
            # Get the mappings corresponding to each pathway queried
            mappings = [
                current_app.manager.get_all_mappings_from_pathway(resource, pathway_id, pathway_name)
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
        return abort(
            500,
            'Not a valid analysis method'
        )


"""Export views"""


@analysis_blueprint.route('/export/<resource>')
def export_gene_set(resource):
    """Export gene set to excel.

    :param str resource: name of the pathway database to visualize its distribution
    """
    resource_manager = current_app.manager_dict.get(resource)

    if not resource_manager:
        return abort(404, '{} resource not found'.format(resource))

    log.info("Querying the database")

    if resource == 'reactome':
        genesets = dict_to_pandas_df(resource_manager.export_gene_sets(species='Homo sapiens'))

    else:
        genesets = dict_to_pandas_df(resource_manager.export_gene_sets())

    sio = StringIO()

    genesets.to_csv(sio)

    output = make_response(sio.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename={}_gene_sets.csv".format(resource)
    output.headers["Content-type"] = "text/csv"
    return output
