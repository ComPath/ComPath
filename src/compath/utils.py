# -*- coding: utf-8 -*-

from pandas import DataFrame, Series
from itertools import combinations
import logging

log = logging.getLogger(__name__)


# modified from https://stackoverflow.com/questions/19736080/creating-dataframe-from-a-dictionary-where-entries-have-different-lengths

def dict_to_pandas_df(d):
    """Transforms pandas df into a dict

    :param dict d:
    :rtype: pandas.DataFrame
    :return: pandas dataframe
    """
    return DataFrame({
        k: Series(list(v))
        for k, v in d.items()
    })


def process_form_gene_set(form_field):
    """Process the string containing gene symbols and returns a gene set

    :param str form_field: string to be processed
    :rtype: set[str]
    :return: geneset
    """
    return {
        gene.strip()
        for line in form_field.split('\n')
        for gene in line.split(',')
    }


def query_gene_set(manager_list, gene_set):
    """

    :param dict manager_list: list of managers
    :param set[str] gene_set: gene set queried
    :return:
    """

    for manager in manager_list.values():
        results = manager.query_gene_set(gene_set)

    return results


def get_gene_sets_from_pathway_names(app, pathways):
    """Returns the gene sets for a given pathway/resource tuple

    :param flask.Flask app: current app
    :param list[tuple[str,str] pathways: pathway/resource tuples
    :rtype: dict
    :return: gene sets
    """

    gene_sets = {}

    for name, resource in pathways:

        manager = app.manager_dict.get(resource.lower())

        pathway = manager.get_pathway_by_name(name)

        if not pathway:
            log.warning('{} pathway not found'.format(name))
            continue

        # Ensure no duplicates are passed
        if name in gene_sets:
            name = "{}_{}".format(name, resource)

        # Check if pathway has no genes
        if not pathway.proteins:
            continue

        gene_sets[name] = {
            protein.hgnc_symbol
            for protein in pathway.proteins
        }

    return gene_sets


def process_overlap_for_venn_diagram(pathway_gene_sets):
    """Calculate gene sets overlaps and process the structure to render venn diagram -> https://github.com/benfred/venn.js/

    :param dict[set] pathway_gene_sets: pathway to gene sets dictionary
    :return: list[dict]
    """

    # Creates future js array with gene sets' lengths
    overlaps_venn_diagram = []

    pathway_to_index = {}
    index = 0

    for name, gene_set in pathway_gene_sets.items():
        overlaps_venn_diagram.append(
            {'sets': [index], 'size': len(gene_set), 'label': name, 'gene_set': list(gene_set)})

        pathway_to_index[name] = index

        index += 1

    for (set_1_name, set_1_values), (set_2_name, set_2_values) in combinations(pathway_gene_sets.items(), r=2):
        overlaps_venn_diagram.append(
            {'sets': [pathway_to_index[set_1_name], pathway_to_index[set_2_name]],
             'size': len(set_1_values.intersection(set_2_values)),
             'gene_set': list(set_1_values.intersection(set_2_values)),
             'label': set_1_name + ' &#8745 ' + set_2_name
             }
        )

    return overlaps_venn_diagram


def get_genes_without_assigned_pathways(manager_list, gene_set):
    """Returns the genes without any known pathway assigned

    :param list manager_list: list of managers
    :param set[str] gene_set: gene set queried
    :return:
    """
    NotImplemented


def parse_pathway_mapping_file(file_path):
    """Parse the pathway mapping file located in resources

    :param str file_path: file path
    :return:
    """
