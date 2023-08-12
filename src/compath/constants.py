# -*- coding: utf-8 -*-

"""Constants for ComPath.

This module contains all the string constants used in ComPath."""

from pkg_resources import DistributionNotFound, get_distribution

from bio2bel.utils import get_connection

DEFAULT_CACHE_CONNECTION = get_connection()

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

ADMIN_EMAIL = 'daniel.domingo.fernandez@scai.fraunhofer.de'

#: Minimum number of votes to accept a mapping
VOTE_ACCEPTANCE = 3

#: Managers without pathway knowledge
BLACKLIST = {
    'hgnc',
    'compath_hgnc',
}

#: Possible mapping types between pathways
MAPPING_TYPES = {
    'equivalentTo',
    'isPartOf',
}

#: Mappings for pathway database
STYLED_NAMES = {
    'kegg': 'KEGG',
    'reactome': 'Reactome',
    'wikipathways': 'WikiPathways',
    'msig': 'MSigDB',
    'pid.pathways': 'Pathway Interaction Database',
    'compath_neurommsig_ad': 'NeuroMMSig AD',
    'compath_neurommsig_pd': 'NeuroMMSig PD',
}

#: Possible mapping types between pathways
EQUIVALENT_TO = 'equivalentTo'
IS_PART_OF = 'isPartOf'

# Check availability of PathMe Viewer
try:
    get_distribution('pathme_viewer')
except DistributionNotFound:
    PATHME = False
else:
    PATHME = True
