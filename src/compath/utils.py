# -*- coding: utf-8 -*-

import logging
from itertools import combinations

import numpy as np
from pandas import DataFrame, Series
from scipy.stats import fisher_exact
from statsmodels.sandbox.stats.multicomp import multipletests

from .constants import BLACK_LIST

log = logging.getLogger(__name__)

"""General utils"""


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
    :return: gene set
    """
    return {
        word.strip().upper()
        for line in form_field.split('\n')
        for word in line.split(',')
        if word
    }


def process_overlap_for_venn_diagram(gene_sets, skip_gene_set_info=False):
    """Calculate gene sets overlaps and process the structure to render venn diagram -> https://github.com/benfred/venn.js/

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


"""Query utils"""


def get_genes_without_assigned_pathways(manager_list, gene_set):
    """Returns the genes without any known pathway assigned

    :param list manager_list: list of managers
    :param set[str] gene_set: gene set queried
    :return:
    """
    NotImplemented


def get_enriched_pathways(manager_list, gene_set):
    """Return the results of the queries for every registered manager

    :param dict[str, Manager] manager_list: list of managers
    :param set[str] gene_set: gene set queried
    :rtype: dict[str,dict[str,dict]]
    """
    return {
        manager_name: instance.query_gene_set(gene_set)
        for manager_name, instance in manager_list.items()
        if manager_name not in BLACK_LIST
    }


def get_pathway_model_by_name(manager_dict, resource, pathway_name):
    """Returns the pathway object from the resource manager

    :param dict manager_dict: manager name to manager instances dictionary
    :param str resource: name of the manager
    :param str pathway_name: pathway name
    :rtype: Optional[Pathway]
    :return: pathway if exists
    """

    manager = manager_dict.get(resource.lower())

    if not manager:
        raise ValueError('Manager does not exist for {}'.format(resource.lower()))

    return manager.get_pathway_by_name(pathway_name)


def get_pathway_model_by_id(app, resource, pathway_id):
    """Returns the pathway object from the resource manager

    :param flask.Flask app: current app
    :param str resource: name of the manager
    :param str pathway_id: pathway id
    :rtype: Optional[Pathway]
    :return: pathway if exists
    """

    manager = app.manager_dict.get(resource.lower())

    return manager.get_pathway_by_id(pathway_id)


def get_gene_sets_from_pathway_names(app, pathways):
    """Returns the gene sets for a given pathway/resource tuple

    :param flask.Flask app: current app
    :param list[tuple[str,str] pathways: pathway/resource tuples
    :rtype: tuple[dict[str,set[str]],dict[str,str]]
    :return: gene sets
    """

    gene_sets = {}

    pathway_manager_dict = {}

    for name, resource in pathways:

        pathway = get_pathway_model_by_name(app.manager_dict, resource, name)

        if not pathway:
            log.warning('{} pathway not found'.format(name))
            continue

        # Ensure no duplicates are passed
        if name in gene_sets:
            name = "{}_{}".format(name, resource)

        # Check if pathway has no genes
        if not pathway.proteins:
            continue

        pathway_manager_dict[name] = resource

        gene_sets[name] = {
            protein.hgnc_symbol
            for protein in pathway.proteins
        }

    return gene_sets, pathway_manager_dict


"""Statistical utils"""


def _prepare_hypergeometric_test(query_gene_set, pathway_gene_set, gene_universe):
    """Prepares the matrix for hypergeometric test calculations

    :param set[str] query_gene_set: gene set to test against pathway
    :param set[str] pathway_gene_set: pathway gene set
    :param int gene_universe: number of HGNC symbols
    :rtype: numpy.ndarray
    :return: 2x2 matrix
    """
    return np.array(
        [[len(query_gene_set.intersection(pathway_gene_set)),
          len(query_gene_set.difference(pathway_gene_set))
          ],
         [len(pathway_gene_set.difference(query_gene_set)),
          gene_universe - len(pathway_gene_set.union(query_gene_set))
          ]
         ]
    )


def perform_hypergeometric_test(gene_set, manager_pathways_dict, gene_universe):
    """

    :param set[str] gene_set: gene set to test against pathway
    :param dict[str,dict[str,dict]] manager_pathways_dict: manager to pathways
    :param int gene_universe: number of HGNC symbols
    :rtype: dict[str,dict[str,dict]]
    :return: manager_pathways_dict with p value info
    """

    manager_p_values = dict()

    for manager_name, pathways in manager_pathways_dict.items():

        for pathway_id, pathway_dict in pathways.items():
            test_table = _prepare_hypergeometric_test(gene_set, pathway_dict["pathway_gene_set"], gene_universe)

            oddsratio, pvalue = fisher_exact(test_table, alternative='greater')

            manager_p_values[manager_name, pathway_id] = pvalue

    # Split the dictionary into names_id tuples and p values to keep the same order
    manager_pathway_id, p_values = zip(*manager_p_values.items())
    correction_test = multipletests(p_values, method='fdr_bh')

    q_values = correction_test[1]

    # Update original dict with p value corrections
    for i, (manager_name, pathway_id) in enumerate(manager_pathway_id):
        manager_pathways_dict[manager_name][pathway_id]["q_value"] = round(q_values[i], 4)

    return manager_pathways_dict


"""Export utils"""


def export_mappings(compath_manager, only_accepted=True):
    """Returns a pandas dataframe with mappings information as an excel sheet file

    :param compath.manager.Manager compath_manager: ComPath Manager
    :param bool only_accepted: only accepted (True) or all (False)
    """

    if only_accepted:
        mappings = compath_manager.get_all_accepted_mappings()
    else:
        mappings = compath_manager.get_all_mappings()

    # TODO: Process here the mappings into data frame

    dataframe = ...

    return dataframe


"""Parser"""


def parse_pathway_mapping_file(file_path):
    """Parse the pathway mapping file located in resources

    :param str file_path: file path
    :return:
    """
