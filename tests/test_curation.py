# -*- coding: utf-8 -*-

""" This module contains tests for the parsing and processing of the curation exercises"""

from compath.curation.curation import _syntax_checker
from .constants import *


class TestCurationParser(unittest.TestCase):

    def test_syntax_checker(self):
        """Testing valid statements"""
        result_1 = _syntax_checker(VALID_MAPPING_1, PATHWAY_X)
        self.assertTrue(result_1)

        result_2 = _syntax_checker(VALID_MAPPING_2, PATHWAY_X)
        self.assertTrue(result_2)

        result_3 = _syntax_checker(VALID_MAPPING_3, PATHWAY_X)
        self.assertTrue(result_3)

    def test_syntax_checker_2(self):
        """Testing unvalid statements"""
        result_1 = _syntax_checker(INVALID_MAPPING_1, PATHWAY_X)
        self.assertFalse(result_1)

        result_2 = _syntax_checker(INVALID_MAPPING_2, PATHWAY_X)
        self.assertFalse(result_2)

        result_3 = _syntax_checker(VALID_MAPPING_2, 'Pathway Y')
        self.assertFalse(result_3)

        result_4 = _syntax_checker(VALID_MAPPING_2, 'pathway X')
        self.assertFalse(result_4)

        result_5 = _syntax_checker(VALID_MAPPING_2, 'pathway X*')
        self.assertFalse(result_5)

        result_6 = _syntax_checker(INVALID_MAPPING_3, '')
        self.assertFalse(result_6)

        result_7 = _syntax_checker(INVALID_MAPPING_4, PATHWAY_X)
        self.assertFalse(result_7)

        result_8 = _syntax_checker(INVALID_MAPPING_5, PATHWAY_X)
        self.assertFalse(result_8)

        result_9 = _syntax_checker(INVALID_MAPPING_6, PATHWAY_X)
        self.assertFalse(result_9)
