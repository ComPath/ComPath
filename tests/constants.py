# -*- coding: utf-8 -*-
"""This module contains all test constants."""

import os
import tempfile
import unittest

from compath.manager import RealManager

# Manager names
KEGG = 'kegg'
REACTOME = 'reactome'

# Curation statements
PATHWAY_X = 'Pathway X'

VALID_MAPPING_1 = 'Pathway X* isPartOf Pathway Parent'
VALID_MAPPING_2 = 'Pathway X equivalentTo Pathway Y'
VALID_MAPPING_3 = 'Pathway X equivalentTo Pathway X'
VALID_MAPPING_4 = '    Pathway X equivalentTo Pathway X'

INVALID_MAPPING_1 = 'Pathway X equivalentto Pathway X'
INVALID_MAPPING_2 = 'Pathway X* ispartof Pathway Parent'
INVALID_MAPPING_3 = ''
INVALID_MAPPING_4 = 'Pathway X isPartOf Pathway Parent'
INVALID_MAPPING_5 = 'Pathway X isPartOfisPartOf Pathway Parent'
INVALID_MAPPING_6 = 'Pathway X isPartOf isPartOf Pathway Parent'
INVALID_MAPPING_7 = []


class DatabaseMixin(unittest.TestCase):
    """Database Mixin."""

    def setUp(self):
        """Create temporary file."""

        self.fd, self.path = tempfile.mkstemp()
        self.connection = 'sqlite:///' + self.path

        # create temporary database
        self.manager = RealManager(connection=self.connection)

    def tearDown(self):
        """Close the connection in the manager and deletes the temporary database."""
        self.manager.drop_all()
        self.manager.session.close()
        os.close(self.fd)
        os.remove(self.path)
