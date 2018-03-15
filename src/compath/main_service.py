# -*- coding: utf-8 -*-

""" This module contains the common views across all pathway bio2bel repos"""

import datetime
import itertools
import logging
import sys
from io import StringIO

from flask import (
    Blueprint,
    render_template,
    make_response,
    flash,
    redirect,
    current_app,
    request,
    jsonify,
    abort
)
from flask_security import current_user, login_required

from .d3_dendrogram import get_dendrogram_tree
from .forms import GeneSetForm
from .utils import (
    dict_to_pandas_df,
    process_form_gene_set,
    get_pathway_model_by_name,
    get_pathway_model_by_id,
    get_enriched_pathways,
    get_gene_sets_from_pathway_names,
    process_overlap_for_venn_diagram
)

log = logging.getLogger(__name__)
time_instantiated = str(datetime.datetime.now())
ui_blueprint = Blueprint('ui', __name__)

"""Main Views"""


@ui_blueprint.route('/', methods=['GET'])
def home():
    """ComPath home page"""
    return render_template('home.html')


@ui_blueprint.route('/imprint', methods=['GET'])
def imprint():
    """Renders the Imprint page"""
    return render_template('imprint.html')


@ui_blueprint.route('/about', methods=['GET'])
def about():
    """Renders About page"""
    metadata = [
        ('Python Version', sys.version),
        ('Deployed', time_instantiated)
    ]

    return render_template('about.html', metadata=metadata)


@ui_blueprint.route('/user', methods=['GET'])
@login_required
def user_activity():
    """Renders the user activity page"""
    return render_template('user/activity.html')


"""Model views"""


@ui_blueprint.route('/pathway/<resource>/<identifier>', methods=['GET'])
def pathway_view(resource, identifier):
    pathway = get_pathway_model_by_id(current_app, resource, identifier)

    return render_template('models/pathway.html', pathway=pathway, resource=resource)


"""Venn Diagram views"""


@ui_blueprint.route('/pathway_overlap', methods=['GET'])
def pathway_overlap():
    """Renders the Pathway Overlap page"""
    return render_template(
        'visualization/venn_diagram/pathway_overlap.html',
        manager_names=current_app.resource_distributions.keys(),
        managers_overlap=current_app.manager_overlap
    )


@ui_blueprint.route('/compare_pathways', methods=['GET'])
def compare_pathways():
    """Renders a venn diagram rendering pathway overlap"""

    if not any(arg in request.args for arg in ("analysis", "pathways[]")):
        return abort(500, 'Invalid request. Missing analysis or pathways[] arguments in the request')

    analysis_type = request.args["analysis"]

    pathways = [
        (pathway.split('|')[1], pathway.split('|')[0])
        for pathway in request.args.getlist('pathways[]')
    ]

    if len(pathways) <= 1:
        return abort(500, 'At least two pathways should be sent as arguments.')

    gene_sets, pathway_manager_dict = get_gene_sets_from_pathway_names(current_app, pathways)

    if not gene_sets:
        return abort(
            500,
            'Pathways could not be found. '
            'Please make sure you have submitted a correct request or contact the administrator'
        )

    if analysis_type == 'venn':

        processed_venn_diagram = process_overlap_for_venn_diagram(gene_sets)

        return render_template(
            'visualization/venn_diagram/pathway_overlap.html',
            venn_diagram_data=processed_venn_diagram
        )

    elif analysis_type == 'dendrogram':

        tree_json, number_of_pathways = get_dendrogram_tree(gene_sets, pathway_manager_dict)

        return render_template(
            'visualization/dendrogram/dendrogram.html',
            tree_json=tree_json,
            numberNodes=number_of_pathways
        )

    elif analysis_type == 'network':
        # TODO: Create new cytoscape template
        return render_template(
            'visualization/similarity_network.html',
            manager_names=current_app.manager_dict.keys(),
        )

    else:
        return abort(
            500,
            'Not a valid analysis method'
        )


"""Cytoscape view"""


@ui_blueprint.route('/similarity_network', methods=['GET'])
def similarity_network():
    """Renders the Similarity network powered by Cytoscape"""
    return render_template(
        'visualization/similarity_network.html',
        manager_names=current_app.manager_dict.keys(),
    )


"""Curation views"""


@ui_blueprint.route('/curation', methods=['GET'])
@login_required
def curation():
    """Renders the curation page"""
    return render_template(
        'curation/create_mapping.html',
        manager_names=current_app.manager_dict.keys(),
    )


@ui_blueprint.route('/mapping_catalog', methods=['GET'])
@login_required
def catalog():
    """Renders the mapping catalog page"""

    return render_template(
        'curation/catalog.html',
        mappings=current_app.manager.get_mappings()
    )


@ui_blueprint.route('/map_pathways', methods=['GET', 'POST'])
@login_required
def process_curation():
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

    flash("Created a mapping between {} and {}".format(pathway_1_model.name, pathway_2_model.name))

    return render_template(
        'curation/create_mapping.html',
        manager_names=current_app.manager_dict.keys(),
    )


"""Clustergrammer views"""


@ui_blueprint.route('/kegg_overlap', methods=['GET'])
def kegg_matrix():
    """Renders the KEGG Matrix page powered by Clustergrammer"""
    return render_template('visualization/clustergrammer/kegg_overlap.html')


@ui_blueprint.route('/reactome_overlap', methods=['GET'])
def reactome_matrix():
    """Renders the Reactome Matrix page powered by Clustergrammer"""
    return render_template('visualization/clustergrammer/reactome_overlap.html')


@ui_blueprint.route('/wikipathways_overlap', methods=['GET'])
def wikipathways_matrix():
    """Renders the WikiPathways Matrix page powered by Clustergrammer"""
    return render_template('visualization/clustergrammer/wikipathways_overlap.html')


@ui_blueprint.route('/pathway_distribution', methods=['GET'])
def pathway_distribution():
    """Renders the Pathway Size distribution page"""
    return render_template(
        'visualization/pathway_distribution.html',
        manager_distribution_dict=current_app.resource_distributions
    )


@ui_blueprint.route('/query', methods=['GET'])
def query():
    """Returns the Query page"""

    form = GeneSetForm()
    return render_template('query.html', form=form)


"""Query views"""


@ui_blueprint.route('/query/overlap', methods=['GET'])
def calculate_overlap():
    """Returns the overlap between different pathways in order to generate a Venn diagram"""

    pathways_list = request.args.getlist('pathways[]')
    resources_list = request.args.getlist('resources[]')

    pathways = list(zip(pathways_list, resources_list))

    if len(pathways) < 2:
        return abort(500, 'Only one set given')

    gene_sets = get_gene_sets_from_pathway_names(current_app, pathways)

    if len(gene_sets) < 2:
        return abort(500, 'Only one valid set given')

    processed_venn_diagram = process_overlap_for_venn_diagram(gene_sets)

    return jsonify(processed_venn_diagram)


@ui_blueprint.route('/query/results', methods=['POST'])
def process_gene_set():
    """Process the gene set POST form"""
    form = GeneSetForm()

    if not form.validate_on_submit():
        flash('The submitted gene set is not valid')
        return redirect('/query')

    gene_sets = process_form_gene_set(form.geneset.data)

    enrichment_results = get_enriched_pathways(current_app.manager_dict, gene_sets)

    return render_template(
        'visualization/enrichment_results.html',
        query_results=enrichment_results,
        submitted_gene_set=gene_sets,
        number_of_pathways=len(list(itertools.chain(*enrichment_results.values())))
    )


# @ui_blueprint.route('/query/upload', methods=('GET', 'POST'))
# def process_geneset_file():
#     """Process uploaded submission"""
#
#     form = GeneSetFileForm()
#
#     if not form.validate_on_submit():
#         return render_template('query.html', form=form)
#
#     df = pd.read_csv(form.file.data)
#
#     gene_column = form.gene_symbol_column.data
#     data_column = form.log_fold_change_column.data
#
#     if gene_column not in df.columns:
#         raise ValueError('{} not a column in document'.format(gene_column))
#
#     if data_column not in df.columns:
#         raise ValueError('{} not a column in document'.format(data_column))
#

"""Export views"""


# TODO switch to export/<name> then look up the manager


@ui_blueprint.route('/export/<resource>', methods=['GET'])
def export_reactome(resource):
    """Export gene set to excel"""

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


"""Autocompletion"""


@ui_blueprint.route('/api/autocompletion/pathway_name', methods=['GET'])
def api_resource_autocompletion():
    """Autocompletion for pathway name"""

    q = request.args.get('q')
    resource = request.args.get('resource')

    if not q or not resource:
        return jsonify([])

    resource = resource.lower()

    manager = current_app.manager_dict.get(resource)

    if not manager:
        return jsonify([])

    return jsonify(list({
        pathway.name
        for pathway in manager.query_pathway_by_name(q, 10)  # Limits the results returned to 10
        if pathway
    }))
