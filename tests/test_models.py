# -*- coding: utf-8 -*-
""" This module contains tests for the data model of ComPath"""

from compath.models import User, Vote, Mapping
from tests.constants import DatabaseMixin, REACTOME, KEGG


class TestMapping(DatabaseMixin):

    def test_create_mapping(self):
        current_user = User()

        mapping_1 = self.manager.get_or_create_mapping(
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
        current_user = User()

        mapping_1 = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            current_user
        )

        mapping_2 = self.manager.get_or_create_mapping(
            REACTOME,
            '2',
            'reactome pathway',
            KEGG,
            '1',
            'kegg pathway',
            current_user
        )

        self.assertEqual(1, self.manager.count_mappings(), msg='The same mapping was added twice')

    def test_create_double_mapping_different_users(self):
        user_1 = User()
        user_2 = User()

        mapping_1 = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            user_1
        )

        mapping_2 = self.manager.get_or_create_mapping(
            REACTOME,
            '2',
            'reactome pathway',
            KEGG,
            '1',
            'kegg pathway',
            user_2
        )

        self.assertEqual(1, self.manager.count_mappings(), msg='The same mapping was added twice')
        self.assertNotEqual(mapping_2.creator, user_2)
        self.assertEqual(mapping_2.creator, user_1)

    def test_vote_up(self):
        current_user = User()

        mapping_1 = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            current_user
        )

        vote = self.manager.get_or_create_vote(user=current_user, mapping=mapping_1)

        self.assertEqual(1, self.manager.count_votes(), msg='Vote was not created')

