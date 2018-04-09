# -*- coding: utf-8 -*-

import unittest

import numpy as np

from compath.visualization.d3_dendrogram import create_similarity_matrix
from compath.visualization.venn_diagram import process_overlap_for_venn_diagram
from compath.utils import (
    process_form_gene_set,
    _prepare_hypergeometric_test,
)


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

    def test_similarity_matrix(self):
        gene_sets = {}

        gene_sets['Pathway1'] = {'A', 'B', 'C', 'D'}
        gene_sets['Pathway2'] = {'C', 'D', 'E'}
        gene_sets['Pathway3'] = {'D', 'F'}

        similarity_matrix = create_similarity_matrix(gene_sets).as_matrix()

        self.assertEqual(
            True,
            np.allclose(np.matrix([
                [1., 0.66666667, 0.5],
                [0.66666667, 1., 0.5],
                [0.5, 0.5, 1.]
            ]),
                similarity_matrix,
            )
        )

    def test_hypergeometric_matrix(self):
        """Test how the matrix gets created"""
        matrix = _prepare_hypergeometric_test({'A', 'B', 'C'}, {'A', 'B', 'C', 'D', 'E', 'F'}, 10)

        self.assertEqual(
            [[3, 0], [3, 4]],
            matrix.tolist()
        )

    def test_venn_diagram_process(self):
        """Venn Diagram"""
        json = process_overlap_for_venn_diagram({'pathway1': {'A', 'B', 'C', 'D', 'E', 'F'}, 'pathway2': {'A', 'B'}})

        self.assertEqual(
           3,
           len(json)
        )