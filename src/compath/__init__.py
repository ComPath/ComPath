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

How to Use
----------

1. Install and load the required packages

- If you just cloned the repo, you can run the sh script "load_compath.sh" by typing :code:`sh load_compath.sh` in your terminal. This script will first install all packages and later populate the database.
- If you have already installed the packages, but not loaded the data. First, load `Bio2BEL HGNC <https://github.com/bio2bel/hgnc>`_ (see next section). Next, load all individual pathway database packages KEGG, Reactome, WikiPathways, and MSigDB  with :code:`python3 -m compath populate`. This command assumes that these packages are already installed in your Python environment. You can check the packages installed by running :code:`python3 -m compath ls` in your terminal. Alternatively, you can populate each package independently by running: :code:`python3 -m bio2bel_kegg populate`, :code:`python3 -m bio2bel_reactome populate`, :code:`python3 -m bio2bel_wikipathways populate`, or :code:`python3 -m bio2bel_msig populate`.

2. The final step is to start the web application locally (runs by default on port 5000 -> http://localhost:5000) by running :code:`python3 -m compath web`

Mapping across gene/protein identifiers
---------------------------------------

In order to load the gene sets from default packages, ComPath assumes that `Bio2BEL HGNC <https://github.com/bio2bel/hgnc>`_
has been already installed and populated. This package is required to perform the mapping from multiple Protein/Gene identifiers to HGNC symbols. The following steps are needed to install Bio2BEL HGNC:

1. :code:`python3 -m pip install bio2bel_hgnc`
2. :code:`python3 -m bio2bel_hgnc populate`



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

__version__ = '0.0.1'

__title__ = 'compath'
__description__ = "A web application for exploring and comparing the overlaps across pathway resources"
__url__ = 'https://github.com/bio2bel/compath'

__author__ = 'Daniel Domingo-Fernández and Charles Tapley Hoyt'
__email__ = 'daniel.domingo.fernandez@scai.fraunhofer.de'

__license__ = 'MIT License'
__copyright__ = 'Copyright (c) 2017-2018 Daniel Domingo-Fernández and Charles Tapley Hoyt'
