# -*- coding: utf-8 -*-

""" This module contains all test constants"""

import os
import tempfile
import unittest

from bio2bel.utils import get_connection
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from compath.constants import MODULE_NAME
from compath.manager import Manager
from compath.models import Base

KEGG = 'kegg'
REACTOME = 'reactome'


class TestManager(Manager):
    def __init__(self, connection=None):
        self.connection = get_connection(MODULE_NAME, connection)
        self.engine = create_engine(self.connection)
        self.session_maker = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
        self.session = self.session_maker()
        self.create_all()

        # Add all available managers

    def create_all(self, check_first=True):
        """Create tables for Bio2BEL KEGG"""
        Base.metadata.create_all(self.engine, checkfirst=check_first)

    def drop_all(self, check_first=True):
        """Drop all tables for Bio2BEL KEGG"""
        Base.metadata.drop_all(self.engine, checkfirst=check_first)


class DatabaseMixin(unittest.TestCase):
    def setUp(cls):
        """Create temporary file"""

        cls.fd, cls.path = tempfile.mkstemp()
        cls.connection = 'sqlite:///' + cls.path

        # create temporary database
        cls.manager = TestManager(connection=cls.connection)

    def tearDown(cls):
        """Closes the connection in the manager and deletes the temporary database"""
        cls.manager.drop_all()
        cls.manager.session.close()
        os.close(cls.fd)
        os.remove(cls.path)
