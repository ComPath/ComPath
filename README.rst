Comparative Pathways Tool |build| |coverage| |docs|
===================================================
An interactive and extensible application for comparative analysis across pathway databases

This package exposes the Bio2BEL pathway packages into a web application containing multiple built-in visualization and
 analytics tools allowing for their analysis and comparison. By default, this packages wraps the following default
 packages:

- `Bio2BEL KEGG <https://github.com/bio2bel/kegg>`_
- `Bio2BEL Reactome <https://github.com/bio2bel/reactome>`_
- `Bio2BEL WikiPathways <https://github.com/bio2bel/wikipathways>`_

New pathway/gene signatures resources can be added by forking the `ComPath Template Repository <https://github.com/bio2bel/compath_template>`_.

Requirements
------------
In order to load the gene sets from default packages, ComPath assumes that `Bio2BEL HGNC <https://github.com/bio2bel/hgnc>`_
has been already installed and populated. This package is required to perform the mapping from multiple Protein/Gene identifiers to HGNC symbols. The following steps are needed to install Bio2BEL HGNC:

1. :code:`python3 -m pip install bio2bel_hgnc`
2. :code:`python3 -m bio2bel_hgnc populate`

Running locally
---------------
1. Load KEGG, Reactome, and WikiPathways in the Bio2BEL database instance. :code:`python3 -m compath populate`.
   These packages should be already installed in your Python environment. You can check the packages installed by
   running :code:`python3 -m compath ls` in your terminal. Alternatively, you can populate each package independently
   by running : :code:`python3 -m bio2bel_kegg populate`, :code:`python3 -m bio2bel_reactome populate`, or
   :code:`python3 -m bio2bel_wikipathways populate`.
2. Start the web app (runs by default http://localhost:5000) with :code:`python3 -m compath web`

.. |build| image:: https://travis-ci.org/bio2bel/ComPath.svg?branch=master
    :target: https://travis-ci.org/bio2bel/compath
    :alt: Build Status

.. |coverage| image:: https://codecov.io/gh/bio2bel/compath/coverage.svg?branch=master
    :target: https://codecov.io/gh/bio2bel/compath?branch=master
    :alt: Coverage Status

.. |docs| image:: http://readthedocs.org/projects/compath/badge/?version=latest
    :target: http://bio2bel.readthedocs.io/projects/compath/en/latest/?badge=latest
    :alt: Documentation Status


