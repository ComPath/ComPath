# -*- coding: utf-8 -*-
""" This module contains all test constants"""

import os
import tempfile
import unittest

from compath.manager import Manager

KEGG = 'kegg'
REACTOME = 'reactome'


class DatabaseMixin(unittest.TestCase):
    def setUp(cls):
        """Create temporary file"""

        cls.fd, cls.path = tempfile.mkstemp()
        cls.connection = 'sqlite:///' + cls.path

        # create temporary database
        cls.manager = Manager(cls.connection)

    def tearDown(cls):
        """Closes the connection in the manager and deletes the temporary database"""
        cls.manager.drop_all()
        cls.manager.session.close()
        os.close(cls.fd)
        os.remove(cls.path)
