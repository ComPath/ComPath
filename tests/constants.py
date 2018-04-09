# -*- coding: utf-8 -*-

""" This module contains all test constants"""

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
    def setUp(cls):
        """Create temporary file"""

        cls.fd, cls.path = tempfile.mkstemp()
        cls.connection = 'sqlite:///' + cls.path

        # create temporary database
        cls.manager = RealManager(connection=cls.connection)

    def tearDown(cls):
        """Closes the connection in the manager and deletes the temporary database"""
        cls.manager.drop_all()
        cls.manager.session.close()
        os.close(cls.fd)
        os.remove(cls.path)
