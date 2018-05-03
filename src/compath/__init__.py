# -*- coding: utf-8 -*-

"""
An interactive and extensible web application for comparative analysis of pathway databases.

This package exposes the Bio2BEL pathway packages into a web application containing multiple built-in visualization and
analytics tools allowing for their analysis and comparison. By default, this packages wraps the following default
packages:

- `Bio2BEL KEGG <https://github.com/bio2bel/kegg>`_
- `Bio2BEL Reactome <https://github.com/bio2bel/reactome>`_
- `Bio2BEL WikiPathways <https://github.com/bio2bel/wikipathways>`_
- `Bio2BEL MSig <https://github.com/bio2bel/msig>`_

New pathway/gene signatures resources can be added by forking the `ComPath Template Repository <https://github.com/compath/compath_template>`_.
"""

import logging

from compath.constants import MODULE_NAME
from compath_utils import CompathManager
from pkg_resources import iter_entry_points, VersionConflict

log = logging.getLogger(__name__)

managers = {}

for entry_point in iter_entry_points(group=MODULE_NAME, name=None):
    entry = entry_point.name

    try:
        bio2bel_module = entry_point.load()
    except VersionConflict:
        log.warning('Version conflict in %s', entry)
        continue

    try:
        ExternalManager = bio2bel_module.Manager
    except AttributeError:
        log.warning('%s does not have a top-level Manager class', entry)
        continue

    if not issubclass(ExternalManager, CompathManager):
        log.warning('%s:%s is not a standard ComPath manager class', entry, ExternalManager)

    managers[entry] = ExternalManager

__version__ = '0.0.1-dev'

__title__ = 'compath'
__description__ = "A web application for exploring and comparing the overlaps across pathway resources"
__url__ = 'https://github.com/bio2bel/compath'

__author__ = 'Daniel Domingo-Fernández and Charles Tapley Hoyt'
__email__ = 'daniel.domingo.fernandez@scai.fraunhofer.de'

__license__ = 'MIT License'
__copyright__ = 'Copyright (c) 2017-2018 Daniel Domingo-Fernández and Charles Tapley Hoyt'
