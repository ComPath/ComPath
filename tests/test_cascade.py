# -*- coding: utf-8 -*-

from compath.constants import EQUIVALENT_TO
from compath.models import User
from tests.constants import DatabaseMixin, KEGG, REACTOME


class TestCascades(DatabaseMixin):
    """Tests that votes are cascaded properly"""

    def setUp(self):
        super().setUp()

        self.u1 = User(email='my_email')
        self.u2 = User(email='my_email_fake')

        self.manager.session.add_all([self.u1, self.u2])
        self.manager.session.commit()

        self.mapping_1, created_1 = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            EQUIVALENT_TO,
            self.u1
        )

        self.mapping_2, created_1 = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway 2',
            REACTOME,
            '2',
            'reactome pathway 2',
            EQUIVALENT_TO,
            self.u2
        )

        v1 = self.manager.get_or_create_vote(self.u2, self.mapping_1)
        v1 = self.manager.get_or_create_vote(self.u1, self.mapping_2)

        self.manager.session.commit()

        self.assertEqual(2, self.manager.count_users())
        self.assertEqual(2, self.manager.count_mappings())
        self.assertEqual(4, self.manager.count_votes())

    def test_drop_all_mappings(self):
        self.manager.delete_all_mappings()

        self.assertEqual(2, self.manager.count_users())
        self.assertEqual(0, self.manager.count_mappings())
        self.assertEqual(0, self.manager.count_votes())

    def test_drop_mapping(self):
        self.manager.session.delete(self.mapping_1)
        self.manager.session.commit()

        self.assertEqual(2, self.manager.count_users())
        self.assertEqual(1, self.manager.count_mappings())
        self.assertEqual(2, self.manager.count_votes())
