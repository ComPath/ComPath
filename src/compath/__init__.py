# -*- coding: utf-8 -*-

import logging
from compath.constants import MODULE_NAME
from pkg_resources import VersionConflict, iter_entry_points

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
        managers[entry] = bio2bel_module.Manager
    except Exception:
        log.warning('%s does not have a top-level Manager class', entry)
        continue

__version__ = '0.0.1-dev'

__title__ = 'compath'
__description__ = "A web application for exploring and comparing the overlaps across pathway resources"
__url__ = 'https://github.com/bio2bel/compath'

__author__ = 'Daniel Domingo-Fernández and Charles Tapley Hoyt'
__email__ = 'daniel.domingo.fernandez@scai.fraunhofer.de'

__license__ = 'MIT License'
__copyright__ = 'Copyright (c) 2017-2018 Daniel Domingo-Fernández and Charles Tapley Hoyt'
