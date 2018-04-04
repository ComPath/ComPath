# -*- coding: utf-8 -*-

""" This module contains tests for the parsing and processing of the curation exercises"""

from compath.constants import *
from compath.curation.utils import statement_syntax_checker, ensure_two_pathways, get_pathways_from_statement
from .constants import *


class TestCurationParser(unittest.TestCase):

    def test_valid_syntax_examples(self):
        """Testing valid statements"""
        result_1 = statement_syntax_checker(VALID_MAPPING_1, PATHWAY_X)
        self.assertTrue(result_1)

        result_2 = statement_syntax_checker(VALID_MAPPING_2, PATHWAY_X)
        self.assertTrue(result_2)

        result_3 = statement_syntax_checker(VALID_MAPPING_3, PATHWAY_X)
        self.assertTrue(result_3)

        result_4 = statement_syntax_checker(VALID_MAPPING_4, PATHWAY_X)
        self.assertTrue(result_4)

    def test_unvalid_syntax_examples(self):
        """Testing unvalid statements"""
        result_1 = statement_syntax_checker(INVALID_MAPPING_1, PATHWAY_X)
        self.assertFalse(result_1)

        result_2 = statement_syntax_checker(INVALID_MAPPING_2, PATHWAY_X)
        self.assertFalse(result_2)

        result_3 = statement_syntax_checker(VALID_MAPPING_2, 'Pathway Y')
        self.assertFalse(result_3)

        result_4 = statement_syntax_checker(VALID_MAPPING_2, 'pathway X')
        self.assertFalse(result_4)

        result_5 = statement_syntax_checker(VALID_MAPPING_2, 'pathway X*')
        self.assertFalse(result_5)

        result_6 = statement_syntax_checker(INVALID_MAPPING_3, '')
        self.assertFalse(result_6)

        result_7 = statement_syntax_checker(INVALID_MAPPING_4, PATHWAY_X)
        self.assertFalse(result_7)

        result_8 = statement_syntax_checker(INVALID_MAPPING_5, PATHWAY_X)
        self.assertFalse(result_8)

        result_9 = statement_syntax_checker(INVALID_MAPPING_6, PATHWAY_X)
        self.assertFalse(result_9)

    def test_two_pathways_in_statement(self):
        """Testing two pathways statements"""
        result_1 = ensure_two_pathways(INVALID_MAPPING_5, IS_PART_OF)
        self.assertFalse(result_1)

        result_2 = ensure_two_pathways(INVALID_MAPPING_6, IS_PART_OF)
        self.assertFalse(result_2)

        result_3 = ensure_two_pathways(VALID_MAPPING_3, EQUIVALENT_TO)
        self.assertTrue(result_3)

    def test_get_pathways_from_statement(self):
        """Testing getting the pathways fr om statements"""
        subject, object = get_pathways_from_statement(VALID_MAPPING_2, EQUIVALENT_TO)

        self.assertEqual(subject, PATHWAY_X)
        self.assertEqual(object, 'Pathway Y')

        subject, object = get_pathways_from_statement(VALID_MAPPING_3, EQUIVALENT_TO)
        self.assertEqual(subject, PATHWAY_X)
        self.assertEqual(object, PATHWAY_X)
