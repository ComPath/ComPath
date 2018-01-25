# -*- coding: utf-8 -*-

""" This module contains the common views across all pathway bio2bel repos"""

import logging

from flask import Blueprint, render_template, send_file, flash, redirect

from bio2bel_kegg.manager import Manager as KeggManager
from bio2bel_reactome.manager import Manager as ReactomeManager
from compath.forms import GeneSetForm
from compath.utils import dict_to_pandas_df, process_form_gene_set, query_gene_set

log = logging.getLogger(__name__)

ui_blueprint = Blueprint('ui', __name__)


@ui_blueprint.route('/', methods=['GET'])
def home():
    """ComPath home page
    """
    return render_template('home.html')


@ui_blueprint.route('/imprint', methods=['GET'])
def imprint():
    """Imprint page
    """
    return render_template('imprint.html')


@ui_blueprint.route('/about', methods=['GET'])
def about():
    """About page
    """
    return render_template('about.html')


"""Query views"""


@ui_blueprint.route('/query', methods=['GET', 'POST'])
def query():
    """Query page
    """
    form = GeneSetForm()
    return render_template('query.html', form=form)


@ui_blueprint.route('/query/process', methods=['POST'])
def process_gene_set():
    """Process the gene set POST form
    """
    form = GeneSetForm()

    if not form.validate_on_submit():
        flash('The submitted gene set is not valid')
        return redirect('/query')

    gene_sets = process_form_gene_set(form.geneset.data)

    enrichment_results = query_gene_set([ReactomeManager(), KeggManager()], gene_sets)

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


@ui_blueprint.route('/reactome/export', methods=['GET', 'POST'])
def export_reactome():
    """Export Reactome gene sets to excel
    """

    reactome_manager = ReactomeManager()

    log.info("Querying the database")

    genesets = dict_to_pandas_df(reactome_manager.export_genesets(species='Homo sapiens'))

    return send_file(
        genesets.to_csv('genesets.csv', index=False),
        mimetype='text/csv',
        attachment_filename='reactome_genesets.csv',
        as_attachment=True
    )


@ui_blueprint.route('/kegg/export', methods=['GET', 'POST'])
def export_kegg():
    """Export KEGG gene sets to excel
    """

    kegg_manager = KeggManager()

    log.info("Querying the database")

    genesets = dict_to_pandas_df(kegg_manager.export_genesets())

    return send_file(
        genesets.to_csv('kegg_genesets.csv', index=False),
        mimetype='text/csv',
        attachment_filename='genesets.csv',
        as_attachment=True
    )
