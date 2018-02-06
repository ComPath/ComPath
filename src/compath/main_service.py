# -*- coding: utf-8 -*-

""" This module contains the common views across all pathway bio2bel repos"""

import logging

from bio2bel_kegg.manager import Manager as KeggManager
from bio2bel_reactome.manager import Manager as ReactomeManager
from flask import Blueprint, render_template, send_file, flash, redirect, current_app, request

from compath import managers
from compath.forms import GeneSetForm
from compath.utils import dict_to_pandas_df, process_form_gene_set, query_gene_set

log = logging.getLogger(__name__)

ui_blueprint = Blueprint('ui', __name__)

"""Main Views"""


@ui_blueprint.route('/', methods=['GET'])
def home():
    """ComPath home page
    """
    return render_template('home.html')


@ui_blueprint.route('/imprint', methods=['GET'])
def imprint():
    """Renders the Imprint page"""
    return render_template('imprint.html')


@ui_blueprint.route('/about', methods=['GET'])
def about():
    """Renders About page"""
    return render_template('about.html')


@ui_blueprint.route('/pathway_overview', methods=['GET'])
def pathway_overview():
    """Renders the Pathway Overview page"""
    return render_template('pathway_comparison_overview.html')


"""Query views"""


@ui_blueprint.route('/query', methods=['GET'])
def query():
    """Returns the Query page"""

    form = GeneSetForm()
    return render_template('query.html', form=form)


@ui_blueprint.route('/query/overlap', methods=['GET'])
def calculate_overlap():
    """Returns the overlap between different pathways in order to generate a Venn diagram"""

    print(request.args)

    # https://github.com/benfred/venn.js/

    NotImplemented


@ui_blueprint.route('/query/process', methods=['POST'])
def process_gene_set():
    """Process the gene set POST form
    """
    form = GeneSetForm()

    if not form.validate_on_submit():
        flash('The submitted gene set is not valid')
        return redirect('/query')

    gene_sets = process_form_gene_set(form.geneset.data)

    manager_instances = [
        Manager(connection=current_app.config.get('COMPATH_CONNECTION'))
        for Manager in managers.values()
    ]

    enrichment_results = query_gene_set(manager_instances, gene_sets)

    print(enrichment_results)

    return redirect('/query')


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


@ui_blueprint.route('/reactome/export', methods=['GET'])
def export_reactome():
    """Export Reactome gene sets to excel"""
    reactome_manager = ReactomeManager(connection=current_app.config.get('COMPATH_CONNECTION'))

    log.info("Querying the database")

    genesets = dict_to_pandas_df(reactome_manager.export_genesets(species='Homo sapiens'))

    return send_file(
        genesets.to_csv('genesets.csv', index=False),
        mimetype='text/csv',
        attachment_filename='reactome_genesets.csv',
        as_attachment=True
    )


@ui_blueprint.route('/kegg/export', methods=['GET'])
def export_kegg():
    """Export KEGG gene sets to excel"""
    kegg_manager = KeggManager(connection=current_app.config.get('COMPATH_CONNECTION'))

    log.info("Querying the database")

    genesets = dict_to_pandas_df(kegg_manager.export_genesets())

    return send_file(
        genesets.to_csv('kegg_genesets.csv', index=False),
        mimetype='text/csv',
        attachment_filename='genesets.csv',
        as_attachment=True
    )
