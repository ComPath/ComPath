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
    'Programming Language :: Python :: 3.7',
    'Topic :: Scientific/Engineering :: Bio-Informatics',
]
INSTALL_REQUIRES = [

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
        f'{MODULE} = {MODULE}.cli:main',
    ]
}


if __name__ == '__main__':
    setuptools.setup()
