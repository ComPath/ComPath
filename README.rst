ComPath |build| |coverage| |docs|
=================================
An interactive and extensible web application for comparative analysis of pathway databases

This package exposes the Bio2BEL pathway packages into a web application containing multiple built-in visualization and
analytics tools allowing for their analysis and comparison. By default, this packages wraps the following default
packages:

- `Bio2BEL KEGG <https://github.com/bio2bel/kegg>`_
- `Bio2BEL Reactome <https://github.com/bio2bel/reactome>`_
- `Bio2BEL WikiPathways <https://github.com/bio2bel/wikipathways>`_
- `Bio2BEL MSIG <https://github.com/bio2bel/msig>`_

New pathway/gene signatures resources can be added by forking the `ComPath Template Repository <https://github.com/compath/compath_template>`_.

How to Use
----------

1. Install and load the required packages

- If you just cloned the repo, you can run the sh script "load_compath.sh" :code:`sh load_compath.sh`.
This will first install all packages and populate the databases.

- Or if you already have installed the packages but not load the databases. First load HGNC in the Bio2BEL database instance (see next section)
and then: KEGG, Reactome, WikiPathways, and MSigDB  with :code:`python3 -m compath populate`.
These packages should be already installed in your Python environment. You can check the packages installed by
running :code:`python3 -m compath ls` in your terminal. Alternatively, you can populate each package independently
by running : :code:`python3 -m bio2bel_kegg populate`, :code:`python3 -m bio2bel_reactome populate`,
:code:`python3 -m bio2bel_wikipathways populate`, or :code:`python3 -m bio2bel_msig populate`.

2. Start the web app locally (runs by default http://localhost:5000) with :code:`python3 -m compath web`

Mapping across gene/protein identifiers
---------------------------------------

In order to load the gene sets from default packages, ComPath assumes that `Bio2BEL HGNC <https://github.com/bio2bel/hgnc>`_
has been already installed and populated. This package is required to perform the mapping from multiple Protein/Gene identifiers to HGNC symbols. The following steps are needed to install Bio2BEL HGNC:

1. :code:`python3 -m pip install bio2bel_hgnc`
2. :code:`python3 -m bio2bel_hgnc populate`



.. |build| image:: https://travis-ci.org/ComPath/ComPath.svg?branch=master
    :target: https://travis-ci.org/ComPath/ComPath
    :alt: Build Status

.. |coverage| image:: https://codecov.io/gh/ComPath/ComPath/coverage.svg?branch=master
    :target: https://codecov.io/gh/ComPath/ComPath?branch=master
    :alt: Coverage Status

.. |docs| image:: http://readthedocs.org/projects/compath/badge/?version=latest
    :target: https://compath.readthedocs.io/en/latest/
    :alt: Documentation Status


