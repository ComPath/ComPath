# -*- coding: utf-8 -*-

"""Utils to generate the Venn Diagram."""

from itertools import combinations


def process_overlap_for_venn_diagram(gene_sets, skip_gene_set_info=False):
    """Calculate gene sets overlaps and process the structure to render venn diagram -> https://github.com/benfred/venn.js/.

    :param dict[str,set] gene_sets: pathway to gene sets dictionary
    :param bool skip_gene_set_info: include gene set overlap data
    :return: list[dict]
    """

    # Creates future js array with gene sets' lengths
    overlaps_venn_diagram = []

    pathway_to_index = {}
    index = 0

    for name, gene_set in gene_sets.items():

        # Only minimum info is returned
        if skip_gene_set_info:
            overlaps_venn_diagram.append(
                {'sets': [index], 'size': len(gene_set), 'label': name.upper()}
            )
        # Returns gene set overlap/intersection information as well
        else:
            overlaps_venn_diagram.append(
                {'sets': [index], 'size': len(gene_set), 'label': name, 'gene_set': list(gene_set)}
            )

        pathway_to_index[name] = index

        index += 1

    # Perform intersection calculations
    for (set_1_name, set_1_values), (set_2_name, set_2_values) in combinations(gene_sets.items(), r=2):
        # Only minimum info is returned
        if skip_gene_set_info:
            overlaps_venn_diagram.append(
                {'sets': [pathway_to_index[set_1_name], pathway_to_index[set_2_name]],
                 'size': len(set_1_values.intersection(set_2_values)),
                 }
            )
        # Returns gene set overlap/intersection information as well
        else:
            overlaps_venn_diagram.append(
                {'sets': [pathway_to_index[set_1_name], pathway_to_index[set_2_name]],
                 'size': len(set_1_values.intersection(set_2_values)),
                 'gene_set': list(set_1_values.intersection(set_2_values)),
                 'intersection': set_1_name + ' &#8745 ' + set_2_name
                 }
            )

    return overlaps_venn_diagram
