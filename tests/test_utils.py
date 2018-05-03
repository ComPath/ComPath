# -*- coding: utf-8 -*-

import math
import unittest

from compath.utils import (
    filter_results,
    get_most_similar_names,
    get_top_matches,
    process_form_gene_set,
    _prepare_hypergeometric_test
)

from compath.visualization.d3_dendrogram import create_similarity_matrix
from compath.visualization.venn_diagram import process_overlap_for_venn_diagram

import numpy as np


class TestUtils(unittest.TestCase):
    """Test utilities."""

    # String matching example
    example_list = [(True, 1.0), (False, 0.5), (False, 0.2), (True, 0.61), (True, 0.7)]

    def test_process_text_area(self):
        """Test processing of text area in form."""
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
        """Test similarity matrix calculations."""
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
        """Test how the matrix gets created."""
        matrix = _prepare_hypergeometric_test({'A', 'B', 'C'}, {'A', 'B', 'C', 'D', 'E', 'F'}, 10)

        self.assertEqual(
            [[3, 0], [3, 4]],
            matrix.tolist()
        )

    def test_venn_diagram_process(self):
        """Test Venn diagram."""
        json = process_overlap_for_venn_diagram({'pathway1': {'A', 'B', 'C', 'D', 'E', 'F'}, 'pathway2': {'A', 'B'}})

        self.assertEqual(
            3,
            len(json)
        )

    """Suggestion based on string matching"""

    def test_filter_results(self):
        """Test suggestion utils."""
        filtered_list = filter_results(self.example_list, 0.6)

        self.assertEqual(
            filtered_list,
            [(True, 1.0), (True, 0.61), (True, 0.7)]
        )

    def test_order_results(self):
        """Test suggestion utils."""

        ordered_list = get_top_matches(self.example_list, 3)

        self.assertEqual(
            ordered_list,
            [(True, 1.0), (True, 0.7), (True, 0.61)]
        )

    def test_get_most_similar(self):
        """Find best matches based on string similarity."""
        most_similar_names = get_most_similar_names(
            'healed',
            ['healed', 'edward', 'sealed', 'theatre', 'non_sense_1', 'non_sense_2', 'non_sense_3', 'non_sense_4',
             'non_sense_5']
        )

        similarity = {
            'healed': 1.0,
            'sealed': 0.8333333333333334,
            'theatre': 0.6153846153846154
        }

        for similar_name, value in most_similar_names:
            self.assertTrue(math.isclose(value, similarity[similar_name]))
