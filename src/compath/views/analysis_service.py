# -*- coding: utf-8 -*-

"""This module contains the analysis views in ComPath."""

import itertools
from io import StringIO
import logging

from compath.constants import BLACK_LIST
from compath.forms import GeneSetForm, GeneSetFileForm
from compath.utils import (
    dict_to_pandas_df,
    get_enriched_pathways,
    get_gene_sets_from_pathway_names,
    get_pathway_info,
    perform_hypergeometric_test,
    process_form_gene_set
)
from compath.visualization.d3_dendrogram import get_dendrogram_tree
from compath.visualization.venn_diagram import process_overlap_for_venn_diagram
from compath.visualization.cytoscape import (
    mappings_to_cytoscape_js,
)
from werkzeug import secure_filename

from flask import (
    abort,
    Blueprint,
    current_app,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request
)

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
        BLACK_LIST=BLACK_LIST
    )


"""Histogram view"""


@analysis_blueprint.route('/pathway_distribution/<resource>')
def pathway_distribution(resource):
    """Render the Pathway Size distribution page.

    :param str resource: name of the pathway database to visualize its distribution
    """
    if resource not in current_app.resource_distributions:
        return abort(500, 'Invalid request. Not a valid manager')

    return render_template(
        'visualization/pathway_distribution.html',
        distribution_data=current_app.resource_distributions[resource],
        resource=resource,
    )


@analysis_blueprint.route('/gene_promiscuity/<resource>')
def gene_distribution(resource):
    """Render how many times genes are present in pathways page.

    :param str resource: name of the pathway database to visualize its distribution
    """
    if resource not in current_app.resource_distributions:
        return abort(500, 'Invalid request. Not a valid manager')

    return render_template(
        'visualization/gene_promiscuity.html',
        distribution_data=current_app.gene_distributions[resource],
        resource=resource,
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

    elif file_form.validate_on_submit():
        gene_sets = process_form_gene_set(file_form.file.data.stream.read().decode("utf-8"))

    else:
        flash('The submitted gene set is not valid')
        return redirect('/query')

    enrichment_results = get_enriched_pathways(current_app.manager_dict, gene_sets)

    # Ensures that submitted genes are in HGNC Manager
    valid_gene_sets = current_app.gene_universe.intersection(gene_sets)

    if valid_gene_sets:
        enrichment_results = perform_hypergeometric_test(valid_gene_sets, enrichment_results,
                                                         len(current_app.gene_universe))
    else:
        flash('ComPath could not find any valid HGNC Symbol from the submitted list')

    return render_template(
        'visualization/enrichment_results.html',
        query_results=enrichment_results,
        submitted_gene_set=valid_gene_sets,
        number_of_pathways=len(list(itertools.chain(*enrichment_results.values())))
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

        # Get the mappings corresponding to each pathway queried
        mappings = [
            current_app.manager.get_all_mappings_from_pathway(resource, pathway_id, pathway_name)
            for resource, pathway_id, pathway_name in pathway_info
        ]

        mappings = [item for sublist in mappings for item in sublist]  # Flat list of lists

        cytoscape_graph = mappings_to_cytoscape_js(mappings)

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
        genesets = dict_to_pandas_df(resource_manager.export_genesets(species='Homo sapiens'))

    else:
        genesets = dict_to_pandas_df(resource_manager.export_genesets())

    sio = StringIO()

    genesets.to_csv(sio)

    output = make_response(sio.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename={}_gene_sets.csv".format(resource)
    output.headers["Content-type"] = "text/csv"
    return output


"""Autocompletion views"""


@analysis_blueprint.route('/api/autocompletion/pathway_name')
def api_resource_autocompletion():
    """Autocompletion for pathway name."""
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
