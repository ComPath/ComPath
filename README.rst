ComPath |build| |coverage| |docs|
=================================
An interactive and extensible web application for comparative analysis of pathway databases

This package exposes the Bio2BEL pathway packages into a web application containing multiple built-in visualization and
analytics tools allowing for their analysis and comparison. By default, this packages wraps the following default
packages:

- `Bio2BEL KEGG <https://github.com/bio2bel/kegg>`_
- `Bio2BEL Reactome <https://github.com/bio2bel/reactome>`_
- `Bio2BEL WikiPathways <https://github.com/bio2bel/wikipathways>`_
- `Bio2BEL MSig <https://github.com/bio2bel/msig>`_

New pathway/gene signatures resources can be added by forking the `ComPath Template Repository <https://github.com/compath/compath_template>`_.

Installation |pypi_version| |python_versions| |pypi_license|
------------------------------------------------------------
``compath`` can be installed easily from `PyPI <https://pypi.python.org/pypi/compath>`_ with the
following code in your favorite terminal:

.. code-block:: sh

    $ python3 -m pip install compath

or from the latest code on `GitHub <https://github.com/compath/compath>`_ with:

.. code-block:: sh

    $ python3 -m pip install git+https://github.com/bio2bel/compath.git@master

Setup
-----
Easiest
~~~~~~~
After installing ``compath``, run from the command line:

.. code-block:: sh

    $ python3 -m compath populate

This command populates all of the relevant Bio2BEL repositories for the default list, and if any optional ComPath
repositories have been registered with entry points, will also populated.

For Developers
~~~~~~~~~~~~~~
If you just cloned the repo and installed it from the source code, you can run the sh script ``load_compath.sh`` by
typing :code:`sh load_compath.sh` in your terminal. This script will first install all packages and later populate the
database.

If you have already installed the packages, but not loaded the data. First, load
`Bio2BEL HGNC <https://github.com/bio2bel/hgnc>`_ (see next section). Next, load all individual pathway database
packages KEGG, Reactome, WikiPathways, and MSigDB  with :code:`python3 -m compath populate`. This command assumes that
these packages are already installed in your Python environment. You can check the packages installed by running
:code:`python3 -m compath ls` in your terminal. Alternatively, you can populate each package independently by running:
:code:`python3 -m bio2bel_kegg populate`, :code:`python3 -m bio2bel_reactome populate`,
:code:`python3 -m bio2bel_wikipathways populate`, or :code:`python3 -m bio2bel_msig populate`.

Curation Interface
------------------
- Load hierarchical mappings from a pathway database already containg that information (e.g., Reactome):

:code:`python3 -m compath load_hierarchies`

- Load mappings from template:

:code:`python3 -m compath add_mappings 'path/to/file/' 'pathway_database_1', pathway_database_2' 'curator_email'`

- Create a user:

:code:`python3 -m compath make_user 'email' 'password'`

- Make user admin:
:code:`python3 -m compath make_admin 'email'`


The web application runs locally by default on port 5000 -> http://localhost:5000).

Mapping across gene/protein identifiers
---------------------------------------

In order to load the gene sets from default packages, ComPath assumes that `Bio2BEL HGNC <https://github.com/bio2bel/hgnc>`_
has been already installed and populated. This package is required to perform the mapping from multiple Protein/Gene identifiers to HGNC symbols. The following steps are needed to install Bio2BEL HGNC:

1. :code:`python3 -m pip install bio2bel_hgnc`
2. :code:`python3 -m bio2bel_hgnc populate`

Running the Web Application
---------------------------
The application can be run simply with

.. code-block:: bash

    python3 -m compath web

This runs the Flask development server locally, by default on port 5000. See http://localhost:5000.

.. |build| image:: https://travis-ci.org/ComPath/ComPath.svg?branch=master
    :target: https://travis-ci.org/ComPath/ComPath
    :alt: Build Status

.. |coverage| image:: https://codecov.io/gh/ComPath/ComPath/coverage.svg?branch=master
    :target: https://codecov.io/gh/ComPath/ComPath?branch=master
    :alt: Coverage Status

.. |docs| image:: http://readthedocs.org/projects/compath/badge/?version=latest
    :target: https://compath.readthedocs.io/en/latest/
    :alt: Documentation Status

.. |climate| image:: https://codeclimate.com/github/compath/compath/badges/gpa.svg
    :target: https://codeclimate.com/github/compath/compath
    :alt: Code Climate

.. |python_versions| image:: https://img.shields.io/pypi/pyversions/compath.svg
    :alt: Stable Supported Python Versions

.. |pypi_version| image:: https://img.shields.io/pypi/v/compath.svg
    :alt: Current version on PyPI

.. |pypi_license| image:: https://img.shields.io/pypi/l/compath.svg
    :alt: MIT License
