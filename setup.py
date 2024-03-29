# -*- coding: utf-8 -*-

"""ComPath setup.py."""

import codecs
import os
import re

import setuptools

MODULE = 'compath'
PACKAGES = setuptools.find_packages(where='src')
META_PATH = os.path.join('src', MODULE, '__init__.py')
KEYWORDS = ['Pathways', 'Systems Biology', 'Networks Biology']
CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.6',
    'Topic :: Scientific/Engineering :: Bio-Informatics'
]
INSTALL_REQUIRES = [
    'click==7.0',
    'sqlalchemy==1.3.3',
    'bio2bel==0.1.5',
    'bio2bel-chebi==0.1.1',
    'bio2bel-hgnc==0.1.2',
    'bio2bel-kegg==0.1.2',
    'bio2bel-reactome==0.1.5',
    'bio2bel-wikipathways==0.1.4',
    'compath_utils==0.2.0',
    'wtforms==2.2.1',
    'flask_wtf==0.14.3',
    'flask==1.0.2',
    'flask-bootstrap==3.3.7.1',
    'flask_admin==1.5.3',
    'flask_security==3.0.0',
    'flask_sqlalchemy==2.3.2',
    'networkx==2.3',
    'pandas==0.24.2',
    'scipy==1.2.1',
    'tqdm==4.31.1',
    'numpy==1.16.3',
    'statsmodels==0.9.0',
    'xlrd==1.2.0',
    'pybel==0.12.1',
    'Werkzeug==0.14.1',
]
EXTRAS_REQUIRE = {
    'docs': [
        'sphinx',
        'sphinx-rtd-theme',
        'sphinx-click',
    ],
}
TESTS_REQUIRE = [
    'bio2bel_kegg',
    'bio2bel_reactome',
    'bio2bel_wikipathways',
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
        classifiers=CLASSIFIERS,
        keywords=KEYWORDS,
        packages=PACKAGES,
        package_dir={'': 'src'},
        include_package_data=True,
        install_requires=INSTALL_REQUIRES,
        extras_require=EXTRAS_REQUIRE,
        tests_require=TESTS_REQUIRE,
        entry_points=ENTRY_POINTS,
    )
