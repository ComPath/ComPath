# -*- coding: utf-8 -*-

""" This module contains tests for the data model of ComPath"""

import unittest

from compath.manager import _flip_service_order
from compath.models import User
from tests.constants import DatabaseMixin, KEGG, REACTOME


class TestServiceOrder(unittest.TestCase):
    def test_same(self):
        self.assertFalse(_flip_service_order(KEGG, KEGG))

    def test_no_flip(self):
        self.assertFalse(_flip_service_order(KEGG, REACTOME))

    def test_flip(self):
        self.assertTrue(_flip_service_order(REACTOME, KEGG))


class TestMapping(DatabaseMixin):
    """Test Mapping in Database"""

    def test_create_mapping(self):
        """Test simple mapping add it"""

        current_user = User()

        mapping_1, _ = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            current_user
        )

        self.assertEqual(1, self.manager.count_mappings(), msg='Mapping was not added')

    def test_create_double_mapping_same_users(self):
        """Test duplicate mappings for same users"""

        current_user = User()

        mapping_1, _ = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            current_user
        )

        mapping_2, created = self.manager.get_or_create_mapping(
            REACTOME,
            '2',
            'reactome pathway',
            KEGG,
            '1',
            'kegg pathway',
            current_user
        )

        self.assertEqual(created, False, msg='The same mapping was added twice')
        self.assertEqual(1, self.manager.count_mappings(), msg='The same mapping was added twice')

    def test_create_double_mapping_different_users(self):
        """Test duplicate mappings for different users"""

        user_1 = User()
        user_2 = User()

        mapping_1, _ = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            user_1
        )

        mapping_2, _ = self.manager.get_or_create_mapping(
            REACTOME,
            '2',
            'reactome pathway',
            KEGG,
            '1',
            'kegg pathway',
            user_2
        )

        self.assertEqual(2, self.manager.count_mappings(), msg='Wrong number of mappings')
        self.assertEqual(mapping_1.creator, user_1)
        self.assertEqual(mapping_2.creator, user_2)

    def test_double_mapping(self):
        """Test double mapping"""

        current_user_1 = User()
        current_user_2 = User()

        mapping_1, _ = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            current_user_1
        )

        mapping_2, _ = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            current_user_2
        )

        self.assertEqual(2, self.manager.count_mappings(), msg='Mappings were not created')
