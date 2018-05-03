# -*- coding: utf-8 -*-

"""This module contains tests for the data model of ComPath."""

from compath.constants import EQUIVALENT_TO
from compath.models import User

from tests.constants import DatabaseMixin, KEGG, REACTOME


class TestVotingSystem(DatabaseMixin):
    """Test Voting System."""

    def test_missing_manager_1(self):
        """Test that the mapping can't be created if the first manager can't be looked up."""
        with self.assertRaises(ValueError):
            self.manager.get_or_create_mapping('missing manager 1', '', '', REACTOME, '', '', '', '')

    def test_missing_manager_2(self):
        """Test that the mapping can't be created if the second manager can't be looked up."""
        with self.assertRaises(ValueError):
            self.manager.get_or_create_mapping(REACTOME, '', '', '' 'missing manager 2', '', '', '', '')

    def test_vote_up(self):
        """Test if votes are adding."""
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

        vote = self.manager.get_or_create_vote(user=current_user, mapping=mapping_1)

        self.assertEqual(1, self.manager.count_votes(), msg='Vote was not created')
        self.assertEqual(True, vote.type, msg='Vote type is wrong')

    def test_vote_down(self):
        """Test if votes are adding."""
        current_user = User()

        mapping_1, created = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            EQUIVALENT_TO,
            current_user
        )
        self.assertTrue(created, msg='Mapping not created')

        vote = self.manager.get_or_create_vote(user=current_user, mapping=mapping_1, vote_type=False)

        self.assertEqual(1, self.manager.count_votes(), msg='Vote was not created')
        self.assertFalse(vote.type, msg='Vote type is wrong')

    def test_double_voting(self):
        """Test voting."""
        current_user_1 = User()
        current_user_2 = User()

        mapping_1, created = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            EQUIVALENT_TO,
            current_user_1
        )

        self.assertTrue(created, 'mapping not created')

        mapping_2, created = self.manager.get_or_create_mapping(
            REACTOME,
            '2',
            'reactome pathway',
            KEGG,
            '1',
            'kegg pathway',
            EQUIVALENT_TO,
            current_user_2
        )

        self.assertFalse(created, 'mapping was created')

        self.assertEqual(2, self.manager.count_votes(), msg='Problem with votes')

        vote_1 = self.manager.get_or_create_vote(user=current_user_1, mapping=mapping_1, vote_type=False)
        vote_2 = self.manager.get_or_create_vote(user=current_user_2, mapping=mapping_2)

        self.assertEqual(2, self.manager.count_votes(), msg='Problem with votes')
        self.assertFalse(vote_1.type, msg='First vote type is wrong')
        self.assertTrue(vote_2.type, msg='Second vote type is wrong')
