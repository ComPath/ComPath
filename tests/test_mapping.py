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
        self.assertEqual(1, self.manager.count_votes(), msg='Vote was not added')

    def test_create_double_mapping_same_users(self):
        """Test duplicate mappings for same users"""

        current_user = User()

        mapping_1, created_1 = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            current_user
        )
        self.assertTrue(created_1, msg='The mapping was not created')

        mapping_2, created_2 = self.manager.get_or_create_mapping(
            REACTOME,
            '2',
            'reactome pathway',
            KEGG,
            '1',
            'kegg pathway',
            current_user
        )

        self.assertEqual(created_2, False, msg='The same mapping was added twice')
        self.assertEqual(1, self.manager.count_mappings(), msg='The same mapping was added twice')
        self.assertEqual(1, self.manager.count_votes(), msg='Vote was not added')

    def test_create_double_mapping_different_users(self):
        """Test duplicate mappings for different users"""

        user_1 = User(email='mycool@email.com')
        user_2 = User(email='myawesome@email.com')

        mapping_1, created = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            user_1
        )

        self.assertTrue(created, 'Mapping not created')

        mapping_2, created = self.manager.get_or_create_mapping(
            REACTOME,
            '2',
            'reactome pathway',
            KEGG,
            '1',
            'kegg pathway',
            user_2
        )

        self.assertFalse(created, 'Mapping not created')
        self.assertEqual(1, self.manager.count_mappings(), msg='Wrong number of mappings')

        emails = [
            user.email
            for user in mapping_1.creators
        ]
        self.assertEqual(emails, [user_1.email, user_2.email])

    def test_export_mappings(self):
        """Test duplicate mappings for different users"""

        user_1 = User(email='mycool@email.com')
        user_2 = User(email='myawesome@email.com')

        mapping_1, created = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            user_1
        )

        mapping_2, created = self.manager.get_or_create_mapping(
            REACTOME,
            '3',
            'reactome pathway',
            KEGG,
            '1',
            'kegg pathway',
            user_2
        )

        mapping_3, created = self.manager.get_or_create_mapping(
            REACTOME,
            '2',
            'reactome pathway',
            KEGG,
            '2',
            'kegg pathway',
            user_2
        )

        mapping_3, accepted = self.manager.accept_mapping(mapping_3.id)

        self.assertTrue(accepted, 'Mapping was not accepted')

        accepted_mappings = self.manager.get_all_accepted_mappings()

        self.assertEqual(accepted_mappings[0], mapping_3, 'Only one mapping was accepted')

        all_mappings = self.manager.get_all_mappings()

        self.assertEqual(
            {mapping_1, mapping_2, mapping_3},
            set(all_mappings),
            'Not all the mappings were fetched'
        )
