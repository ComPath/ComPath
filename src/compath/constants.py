# -*- coding: utf-8 -*-

"""Constants for ComPath.

This module contains all the string constants used in ComPath."""

import os

from bio2bel.utils import get_connection, get_data_dir

MODULE_NAME = 'compath'
DATA_DIR = get_data_dir(MODULE_NAME)
DEFAULT_CACHE_CONNECTION = get_connection(MODULE_NAME)

SWAGGER_CONFIG = {
    'title': 'ComPath API',
    'description': 'Exposes the ComPath RESTful API',
    'contact': {
        'responsibleOrganization': 'Fraunhofer SCAI',
        'responsibleDeveloper': 'Daniel Domingo-Fernandez',
        'email': 'daniel.domingo.fernandez@scai.fraunhofer.de',
        'url': 'https://www.scai.fraunhofer.de/de/geschaeftsfelder/bioinformatik.html',
    },
    'version': '0.1.0',
}

# Static files

dir_path = os.path.dirname(os.path.realpath(__file__))
STATIC_FOLDER = os.path.join(dir_path, 'static')

EXCEL_FOLDER = os.path.join(STATIC_FOLDER, 'resources', 'excel')

#: CSV file for Reactome gene set
REACTOME_GENE_SET = os.path.join(EXCEL_FOLDER, 'kegg_gene_sets.csv')

#: CSV file for KEGG gene set
KEGG_GENE_SET = os.path.join(EXCEL_FOLDER, 'reactome_gene_sets.csv')

#: CSV file for WikiPathways gene set
WIKIPATHWAYS_GENE_SET = os.path.join(EXCEL_FOLDER, 'wikipathways_gene_sets.csv')

#: CSV file for MSigDB gene set
MSIG_GENE_SET = os.path.join(EXCEL_FOLDER, 'msig_gene_sets.csv')

ADMIN_EMAIL = 'daniel.domingo.fernandez@scai.fraunhofer.de'

#: Minimum number of votes to accept a mapping
VOTE_ACCEPTANCE = 3

#: KEGG
KEGG = 'kegg'

#: Reactome
REACTOME = 'reactome'

#: WikiPathways
WIKIPATHWAYS = 'wikipathways'

#: MSigDB
MSIG = 'msig'

#: REST API to KEGG
KEGG_URL = 'http://www.kegg.jp/kegg-bin/show_pathway?map=map{}&show_description=show'

#: URL to pathways in Reactome
REACTOME_URL = 'https://reactome.org/PathwayBrowser/#/{}'

#: URL to pathways in WikiPathways
WIKIPATHWAYS_URL = 'https://www.wikipathways.org/index.php/Pathway:{}'

#: Managers with hierarchical information
HIERARCHY_MANAGERS = {REACTOME}

#: Managers without pathway knowledge
BLACK_LIST = {
    'hgnc',
    'compath_hgnc',
}

#: Possible mapping types between pathways
MAPPING_TYPES = {
    'equivalentTo',
    'isPartOf'
}

#: Mappings for pathway database
STYLED_NAMES = {
    KEGG: 'KEGG',
    REACTOME: 'Reactome',
    WIKIPATHWAYS: 'WikiPathways',
    MSIG: 'MSig',
    'compath_neurommsig_ad': 'NeuroMMSig AD',
    'compath_neurommsig_pd': 'NeuroMMSig PD'

}

#: Possible mapping types between pathways
EQUIVALENT_TO = 'equivalentTo'
IS_PART_OF = 'isPartOf'
