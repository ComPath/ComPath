ComPath (Comparative Pathways Tool) |build| |coverage| |docs|
=============================================================

A web application for exploring and comparing the overlaps across pathway resources.
So far, this packages wraps the following packages:

- `Bio2BEL KEGG <https://github.com/bio2bel/kegg>`_
- `Bio2BEL Reactome <https://github.com/bio2bel/reactome>`_

Requirements
------------

In order to load the gene sets from both packages, ComPath assumes that `Bio2BEL HGNC <https://github.com/bio2bel/hgnc>`_
has been already installed and populated. The following steps are needed to install Bio2BEL HGNC:

1. :code:`python3 -m pip install bio2bel_hgnc`

2. :code:`python3 -m bio2bel_hgnc populate`

Running locally
---------------

1. Load KEGG and Reactome in database. :code:`python3 -m compath populate`

2. Run the web app (by default in port `5000 <http://localhost:5000/`_). :code:`python3 -m compath web`


.. |build| image:: https://travis-ci.org/bio2bel/reactome.svg?branch=master
    :target: https://travis-ci.org/bio2bel/compath
    :alt: Build Status

.. |coverage| image:: https://codecov.io/gh/bio2bel/compath/coverage.svg?branch=master
    :target: https://codecov.io/gh/bio2bel/compath?branch=master
    :alt: Coverage Status

.. |docs| image:: http://readthedocs.org/projects/compath/badge/?version=latest
    :target: http://bio2bel.readthedocs.io/projects/compath/en/latest/?badge=latest
    :alt: Documentation Status


