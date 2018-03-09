# -*- coding: utf-8 -*-

import unittest

from compath.utils import process_form_gene_set


class TestUtils(unittest.TestCase):
    def test_process_text_area(self):
        query_test = ",,,GENE1_COMMA,  GENE2_COMMA\n     GENE3_NEW_LINE\n   GENE4_NEW_LINE, gene5_comma"

        processed_query = process_form_gene_set(query_test)

        self.assertEqual(
            processed_query,
            {
                'GENE1_COMMA',
                'GENE2_COMMA',
                'GENE3_NEW_LINE',
                'GENE4_NEW_LINE',
                'GENE5_COMMA'
            }
        )
