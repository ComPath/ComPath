# -*- coding: utf-8 -*-

"""This module contains tests for the data model of ComPath"""

import unittest

from tests.constants import DatabaseMixin, KEGG, REACTOME

from compath.constants import EQUIVALENT_TO, IS_PART_OF
from compath.manager import _flip_service_order
from compath.models import User


class TestServiceOrder(unittest.TestCase):
    """Test alphabetical order of the services."""

    def test_same(self):
        """Test same resource so it does not flip them."""
        self.assertFalse(_flip_service_order(KEGG, KEGG))

    def test_no_flip(self):
        """Test right order so it does not flip them."""
        self.assertFalse(_flip_service_order(KEGG, REACTOME))

    def test_flip(self):
        """Test wrong order so it does flip them."""
        self.assertTrue(_flip_service_order(REACTOME, KEGG))


class TestMapping(DatabaseMixin):
    """Test Mapping in Database"""

    def test_create_mapping(self):
        """Test simple mapping add it."""
        current_user = User()

        mapping_1, _ = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            EQUIVALENT_TO,
            current_user
        )

        self.assertEqual(1, self.manager.count_mappings(), msg='Mapping was not added')
        self.assertEqual(1, self.manager.count_votes(), msg='Vote was not added')

    def test_create_double_mapping_same_users(self):
        """Test duplicate mappings for same users."""

        current_user = User()

        mapping_1, created_1 = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            EQUIVALENT_TO,
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
            EQUIVALENT_TO,
            current_user
        )

        self.assertFalse(created_2, msg='The same mapping was added twice')

        self.assertEqual(1, self.manager.count_mappings(), msg='The same mapping was added twice')
        self.assertEqual(1, self.manager.count_votes(), msg='Vote was not added')

        mapping_3, created_3 = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            IS_PART_OF,
            current_user
        )
        self.assertTrue(created_3, msg='The mapping was not created')

        mapping_4, created_4 = self.manager.get_or_create_mapping(
            REACTOME,
            '2',
            'reactome pathway',
            KEGG,
            '1',
            'kegg pathway',
            IS_PART_OF,
            current_user
        )

        self.assertTrue(created_4, msg='The mapping was not created')

        mapping_5, created_5 = self.manager.get_or_create_mapping(
            REACTOME,
            '2',
            'reactome pathway',
            KEGG,
            '1',
            'kegg pathway',
            IS_PART_OF,
            current_user
        )

        self.assertFalse(created_5, msg='A duplicate mapping was created')

        self.assertEqual(3, self.manager.count_mappings(), msg='Something wrong with isPartOf mappings')
        self.assertEqual(3, self.manager.count_votes(), msg='Something wrong with isPartOf mappings')

    def test_create_double_mapping_different_users(self):
        """Test duplicate mappings for different users."""
        user_1 = User(email='mycool@email.com')
        user_2 = User(email='myawesome@email.com')

        mapping_1, created = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            EQUIVALENT_TO,
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
            EQUIVALENT_TO,
            user_2
        )

        self.assertFalse(created, 'Mapping not created')
        self.assertEqual(1, self.manager.count_mappings(), msg='Wrong number of mappings')

        emails = [
            user.email
            for user in mapping_1.creators
        ]
        self.assertEqual(emails, [user_1.email, user_2.email])

    def test_get_accepted_mappings(self):
        """Test duplicate mappings for different users."""

        user_1 = User(email='mycool@email.com')
        user_2 = User(email='myawesome@email.com')

        mapping_1, created = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            EQUIVALENT_TO,
            user_1
        )

        mapping_2, created = self.manager.get_or_create_mapping(
            REACTOME,
            '3',
            'reactome pathway',
            KEGG,
            '1',
            'kegg pathway',
            EQUIVALENT_TO,
            user_2
        )

        mapping_3, created = self.manager.get_or_create_mapping(
            REACTOME,
            '2',
            'reactome pathway',
            KEGG,
            '2',
            'kegg pathway',
            EQUIVALENT_TO,
            user_2
        )

        mapping_3, accepted = self.manager.accept_mapping(mapping_3.id)

        self.assertTrue(accepted, 'Mapping was not accepted')

        # Checks all mappings
        all_mappings = self.manager.get_all_mappings()

        self.assertEqual(
            {mapping_1, mapping_2, mapping_3},
            set(all_mappings),
            'Not all the mappings were fetched'
        )

        # Checks only accepted mappings

        accepted_mappings = self.manager.get_all_accepted_mappings()

        self.assertIsNotNone(accepted_mappings[0], msg='No mappings were fetched')

        self.assertEqual(accepted_mappings[0], mapping_3, 'Only one mapping was accepted')

    def test_create_double_mapping_different_types_same_users(self):
        """Test duplicate mappings for same users."""
        current_user = User()

        mapping_1, created_1 = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            EQUIVALENT_TO,
            current_user
        )
        self.assertTrue(created_1, msg='The mapping was not created')

        mapping_2, created_2 = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            IS_PART_OF,
            current_user
        )

        self.assertTrue(created_2, msg='The same mapping was added twice')
        self.assertEqual(2, self.manager.count_mappings(), msg='Only one mapping was created')
        self.assertEqual(2, self.manager.count_votes(), msg='Problem with voting')

        result_1 = self.manager.get_mappings_from_pathway_with_relationship(EQUIVALENT_TO, REACTOME, '2',
                                                                            'reactome pathway')
        self.assertEqual(result_1[0], mapping_1, msg='Query not working')
        self.assertIn(mapping_1, result_1, msg='Query not working')

        result_2 = self.manager.get_mappings_from_pathway_with_relationship(IS_PART_OF, REACTOME, '2',
                                                                            'reactome pathway')
        self.assertEqual(result_2[0], mapping_2, msg='Query not working')
        self.assertIn(mapping_2, result_2, msg='Query not working')
