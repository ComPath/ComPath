# -*- coding: utf-8 -*-

"""This module contains tests for the parsing and processing of the curation exercises."""

import unittest

from compath.constants import EQUIVALENT_TO
from compath.curation.utils import (
    get_pathways_from_statement,
    remove_star_from_pathway_name
)
from tests.constants import *


class TestCurationParser(unittest.TestCase):
    """Test Curation Parser."""

    def test_get_pathways_from_statement(self):
        """Testing getting the pathways fr om statements."""
        subject, object = get_pathways_from_statement(VALID_MAPPING_2, EQUIVALENT_TO)

        self.assertEqual(subject, PATHWAY_X)
        self.assertEqual(object, 'Pathway Y')

        subject, object = get_pathways_from_statement(VALID_MAPPING_3, EQUIVALENT_TO)
        self.assertEqual(subject, PATHWAY_X)
        self.assertEqual(object, PATHWAY_X)

    def test_remove_star(self):
        """Test get mapping type."""
        result_1 = remove_star_from_pathway_name(VALID_MAPPING_1)

        self.assertEqual(result_1, 'Pathway X isPartOf Pathway Parent')
