# -*- coding: utf-8 -*-

from pandas import DataFrame, Series


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


def calculate_pathway_overlap(pathways):

    for pathway, resource in pathways:

        print(pathway, resource)



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
