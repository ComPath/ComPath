# -*- coding: utf-8 -*-

"""ComPath setup.py."""

import codecs
import os
import re

import setuptools

MODULE = 'compath'
PACKAGES = setuptools.find_packages(where='src')
META_PATH = os.path.join('src', MODULE, '__init__.py')
INSTALL_REQUIRES = [
    'click',
    'sqlalchemy==1.1.15',
    'pandas',
    'bio2bel>=0.0.9',
    'compath_utils>=0.0.3',
    'bio2bel_hgnc',
    'bio2bel_kegg>=0.0.6',
    'bio2bel_reactome>=0.0.5',
    'bio2bel_wikipathways>=0.0.6',
    'bio2bel_msig>=0.0.2',
    'wtforms',
    'flask_wtf',
    'flask',
    'flask-bootstrap',
    'flask_admin',
    'flask_security',
    'flask_sqlalchemy',
    'scipy',
    'numpy',
    'statsmodels',
    'xlrd'
]
ENTRY_POINTS = {
    'console_scripts': [
        '{mname} = {mname}.cli:main'.format(mname=MODULE),
    ]
}

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """Build an absolute path from *parts* and return the contents of the resulting file. Assume UTF-8 encoding."""
    with codecs.open(os.path.join(HERE, *parts), 'rb', 'utf-8') as f:
        return f.read()


META_FILE = read(META_PATH)


def find_meta(meta):
    """Extract __*meta*__ from META_FILE."""
    meta_match = re.search(
        r'^__{meta}__ = ["\']([^"\']*)["\']'.format(meta=meta),
        META_FILE, re.M
    )
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError('Unable to find __{meta}__ string'.format(meta=meta))


def get_long_description():
    """Get the long_description from the README.rst file. Assume UTF-8 encoding."""
    with codecs.open(os.path.join(HERE, 'README.rst'), encoding='utf-8') as f:
        long_description = f.read()
    return long_description


if __name__ == '__main__':
    setuptools.setup(
        name=find_meta('title'),
        version=find_meta('version'),
        description=find_meta('description'),
        long_description=get_long_description(),
        url=find_meta('url'),
        author=find_meta('author'),
        author_email=find_meta('email'),
        maintainer=find_meta('author'),
        maintainer_email=find_meta('email'),
        license=find_meta('license'),
        packages=PACKAGES,
        package_dir={'': 'src'},
        install_requires=INSTALL_REQUIRES,
        entry_points=ENTRY_POINTS,
    )
