# -*- coding: utf-8 -*-

""" This module contains the common views across all pathway bio2bel repos"""

import logging

from flask import Blueprint, render_template, send_file

from bio2bel_reactome.manager import Manager as ReactomeManager
from bio2bel_kegg.manager import Manager as KeggManager
from compath.utils import dict_to_pandas_df

log = logging.getLogger(__name__)

ui_blueprint = Blueprint('ui', __name__)


@ui_blueprint.route('/', methods=['GET', 'POST'])
def home():
    """ComPath home page
    """
    return render_template('home.html')


@ui_blueprint.route('/imprint', methods=['GET', 'POST'])
def imprint():
    """Imprint page
    """
    return render_template('imprint.html')


@ui_blueprint.route('/about', methods=['GET', 'POST'])
def about():
    """About page
    """
    return render_template('about.html')


@ui_blueprint.route('/reactome/export', methods=['GET', 'POST'])
def export_reactome():
    """Export Reactome gene sets to excel
    """

    m = ReactomeManager()

    log.info("Querying the database")

    genesets = dict_to_pandas_df(m.export_genesets())

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

    m = KeggManager()

    log.info("Querying the database")

    genesets = dict_to_pandas_df(m.export_genesets())

    return send_file(
        genesets.to_csv('kegg_genesets.csv', index=False),
        mimetype='text/csv',
        attachment_filename='genesets.csv',
        as_attachment=True
    )