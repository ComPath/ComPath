# -*- coding: utf-8 -*-

"""An interactive and extensible web application for comparative analysis of pathway databases.

ComPath is available at https://compath.scai.fraunhofer.de/.

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

- If you just cloned the repo, you can run the sh script "load_compath.sh" by typing :code:`sh load_compath.sh` in
  your terminal. This script will first install all packages and later populate the database.
- If you have already installed the packages, but not loaded the data. Load all individual pathway database packages
  KEGG, Reactome, WikiPathways, and MSigDB  with :code:`python3 -m compath populate`. This command assumes that
  these packages are already installed in your Python environment. You can check the packages installed by running
  :code:`python3 -m compath ls` in your terminal. Alternatively, you can populate each package independently by
  running: :code:`python3 -m bio2bel_kegg populate`, :code:`python3 -m bio2bel_reactome populate`,
  :code:`python3 -m bio2bel_wikipathways populate`, or :code:`python3 -m bio2bel_msig populate`.

2. The final step is to start the web application locally (runs by default on port 5000 -> http://localhost:5000) by
   running :code:`python3 -m compath web`
"""

import logging

from pkg_resources import DistributionNotFound, get_distribution

from bio2bel.compath import get_compath_manager_classes
from compath.constants import MODULE_NAME

logger = logging.getLogger(__name__)

# Load Bio2BEL ComPath managers
managers = get_compath_manager_classes()

# Check availability of PathMe Viewer
try:
    get_distribution('pathme_viewer')
    PATHME = True
except DistributionNotFound:
    PATHME = False
