# -*- coding: utf-8 -*-

"""This module contains miscellaneous methods."""

import logging
from collections import defaultdict
from difflib import SequenceMatcher

import numpy as np
from pandas import DataFrame, Series
from scipy.stats import fisher_exact
from statsmodels.sandbox.stats.multicomp import multipletests
from compath.models import User

from .constants import BLACK_LIST

log = logging.getLogger(__name__)

"""General utils"""


# modified from https://stackoverflow.com/questions/19736080/creating-dataframe-from-a-dictionary-where-entries-have-different-lengths

def dict_to_pandas_df(d):
    """Transform pandas df into a dict.

    :param dict d:
    :rtype: pandas.DataFrame
    :return: pandas dataframe
    """
    return DataFrame({
        k: Series(list(v))
        for k, v in d.items()
    })


def process_form_gene_set(text):
    """Process the string containing gene symbols and returns a gene set.

    :param str text: string to be processed
    :rtype: set[str]
    :return: gene set
    """
    return {
        word.strip().upper()
        for line in text.split('\n')
        for word in line.split(',')
        if word
    }


"""Simulation of pathway enrichment.
This set of methods perform a simulation of pathway enrichment. Given a genes, it calculates how many pathways
have at least x genes in a pathway.
"""


def calculate_relative_enrichments(results, total_pathways_by_resource):
    """Calculate relative enrichment of pathways (enriched pathways/total pathways).

    :param dict results: result enrichment
    :param dict total_pathways_by_resource: resource to number of pathways
    :rtype: dict
    """
    return {
        resource: len(enriched_pathways) / total_pathways_by_resource[resource]
        for resource, enriched_pathways in results.items()
    }


def count_genes_in_pathway(pathways_gene_sets, genes):
    """Calculate how many of the genes are associated to each pathway gene set.

    :param dict pathways_gene_sets: pathways and their gene sets
    :param set genes: genes queried
    :rtype: dict
    """
    return {
        pathway: len(gene_set.intersection(genes))
        for pathway, gene_set in pathways_gene_sets.items()
    }


def apply_filter(results, threshold):
    """Run one simulation with a given threshold.

    :param dict results: resource with pathways
    :param int threshold: necessary genes to enrich a pathway
    :rtype: dict
    """
    filtered_results = {}

    for database_name, pathways in results.items():

        pathways_pass_filter = []

        for pathway_name, genes_mapped in pathways.items():

            if genes_mapped < threshold:
                continue

            pathways_pass_filter.append(pathway_name)

        filtered_results[database_name] = pathways_pass_filter

    return filtered_results


def simulate_pathway_enrichment(resource_gene_sets, gene_set_query, runs=200):
    """Simulate pathway enrichment.

    :param resource_gene_sets: resource and their gene sets
    :param gene_set_query: shared genes between all resources
    :param runs: number of simulation
    :rtype: dict[list[tuple]]
    """

    # How many pathways each resource (Database) has
    total_pathways_by_resource = {
        resource: len(pathways_gene_sets)
        for resource, pathways_gene_sets in resource_gene_sets.items()
    }

    # How many genes of the 'gene_set_query' are in each pathway
    enriched_pathways = {
        resource: count_genes_in_pathway(pathways_gene_sets, gene_set_query)
        for resource, pathways_gene_sets in resource_gene_sets.items()
    }

    results = defaultdict(list)

    # Calculate the percentage of pathways in the database with a minimum of genes in the pathway
    for threshold in range(1, runs):
        filtered_results = apply_filter(enriched_pathways, threshold)

        relative_enrichments = calculate_relative_enrichments(
            filtered_results, total_pathways_by_resource
        )

        for resource, result in relative_enrichments.items():
            results[resource].append(round(result, 3))

    return results


"""Query utils"""


def _iterate_user_strings(manager_):
    """Iterates over strings to print describing users
    :param compath.manager.Manager manager_:
    :rtype: iter[str]
    """
    for user in manager_.session.query(User).all():
        yield '{email}\t{password}\t{roles}'.format(
            email=user.email,
            password=user.password,
            roles=','.join(sorted(r.name for r in user.roles)),
        )


def get_genes_without_assigned_pathways(enrichment_results, genes_query):
    """Returns the genes without any known pathway assigned.

    :param dict gene_set: list of managers
    :param set[str] genes_query: gene set queried
    :return:
    """
    # Get genes in all pathways
    genes_in_pathways = {
        gene
        for resource_pathways in enrichment_results.values()
        for pathway_dict in resource_pathways.values()
        for gene in pathway_dict['pathway_gene_set']
    }
    # Find the genes not in pathways
    return {
        gene
        for gene in genes_query
        if gene not in genes_in_pathways
    }


def get_enriched_pathways(manager_list, gene_set):
    """Return the results of the queries for every registered manager.

    :param dict[str, Manager] manager_list: list of managers
    :param set[str] gene_set: gene set queried
    :rtype: dict[str,dict[str,dict]]
    """
    return {
        manager_name: instance.query_gene_set(gene_set)
        for manager_name, instance in manager_list.items()
        if manager_name not in BLACK_LIST
    }

def get_gene_pathways(manager_list, gene):
    """Return the pathways associated with a gene for every registered manager.

    :param dict[str, Manager] manager_list: list of managers
    :param str gene: HGNC symbol
    :rtype: dict[str,dict[str,dict]]
    """
    return {
        manager_name: instance.query_gene(gene)
        for manager_name, instance in manager_list.items()
        if manager_name not in BLACK_LIST
    }


def get_mappings(compath_manager, only_accepted=True):
    """Return a pandas dataframe with mappings information as an excel sheet file.

    :param compath.manager.Manager compath_manager: ComPath Manager
    :param bool only_accepted: only accepted (True) or all (False)
    """
    if only_accepted:
        mappings = compath_manager.get_all_accepted_mappings()
    else:
        mappings = compath_manager.get_all_mappings()

    return [
        (
            mapping.service_1_pathway_name,
            mapping.service_1_pathway_id,
            mapping.service_1_name,
            mapping.type,
            mapping.service_2_pathway_name,
            mapping.service_2_pathway_id,
            mapping.service_2_name
        )
        for mapping in mappings
    ]


def get_pathway_model_by_name(manager_dict, resource, pathway_name):
    """Return the pathway object from the resource manager.

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
    """Return the pathway object from the resource manager.

    :param flask.Flask app: current app
    :param str resource: name of the manager
    :param str pathway_id: pathway id
    :rtype: Optional[Pathway]
    :return: pathway if exists
    """
    manager = app.manager_dict.get(resource.lower())

    return manager.get_pathway_by_id(pathway_id)


def get_gene_sets_from_pathway_names(app, pathways):
    """Return the gene sets for a given pathway/resource tuple.

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


def get_pathway_info(app, pathways):
    """Return the gene sets for a given pathway/resource tuple.

    :param flask.Flask app: current app
    :param list[tuple[str,str] pathways: pathway/resource tuples
    :rtype: list
    :return: pathway info
    """
    pathway_info = []

    for name, resource in pathways:

        pathway = get_pathway_model_by_name(app.manager_dict, resource, name)

        if not pathway:
            log.warning('{} pathway not found'.format(name))
            continue

        pathway_info.append((resource, pathway.resource_id, pathway.name))

    return pathway_info


"""Statistical utils"""


def _prepare_hypergeometric_test(query_gene_set, pathway_gene_set, gene_universe):
    """Prepare the matrix for hypergeometric test calculations.

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


def perform_hypergeometric_test(gene_set, manager_pathways_dict, gene_universe, apply_threshold=False, threshold=0.05):
    """Perform hypergeometric tests

    :param set[str] gene_set: gene set to test against pathway
    :param dict[str,dict[str,dict]] manager_pathways_dict: manager to pathways
    :param int gene_universe: number of HGNC symbols
    :param Optional[bool] apply_threshold: return only significant pathways
    :param Optional[float] threshold: significance threshold (by default 0.05)
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

        q_value = round(q_values[i], 4)
        manager_pathways_dict[manager_name][pathway_id]["q_value"] = q_value

        # [Optional] Delete the pathway if does not pass the threshold
        if apply_threshold and q_value > threshold:
            del manager_pathways_dict[manager_name][pathway_id]

    return manager_pathways_dict


"""Suggestion utils"""


def calculate_szymkiewicz_simpson_coefficient(set_1, set_2):
    """Calculate Szymkiewicz-Simpson coefficient between two sets.

    :param set set_1: set 1
    :param set set_2: set 2
    :return: similarity of the two sets
    :rtype: float
    """

    intersection = len(set_1.intersection(set_2))
    smaller_set = min(len(set_1), len(set_2))

    return intersection / smaller_set


def calculate_similarity(name_1, name_2):
    """Calculate the string based similarity between two names.

    :param str name_1: name 1
    :param str name_2: name 2
    :rtype: float
    :return: Levenshtein similarity
    """
    return SequenceMatcher(None, name_1, name_2).ratio()


def get_top_matches(matches, top):
    """Order list of tuples by second value and returns top values.

    :param list[tuple[str,float]] matches: list of tuples
    :param int top: top values to return
    """
    sorted_names = sorted(matches, key=lambda x: x[1], reverse=True)

    return sorted_names[0:top]


def filter_results(results, threshold):
    """Filter a tuple based iterator given a threshold.

    :param list[tuple[str,float]] results: list of tuples
    :param float threshold: thresholding
    """
    return [
        (name, value)
        for name, value in results
        if value > threshold
    ]


def get_most_similar_names(reference_name, names, threshold=0.4, top=5):
    """Return the most similar names based on string matching.

    :param str reference_name:
    :param list[str] names:
    :param optional[float] threshold:
    :param optional[int] top:
    :return:
    """
    string_matching = [
        (name, calculate_similarity(reference_name, name))
        for name in names
    ]

    most_similar_names = filter_results(string_matching, threshold)

    # Order pathways by descendent similarity
    return get_top_matches(most_similar_names, top)


"""Export utils"""


def to_csv(triplets, file=None, sep='\t'):
    """Writs triplets as a tab-separated.

    :param iterable[tuple[str,str,str]] triplets: iterable of triplets
    :param file file: A writable file or file-like. Defaults to stdout.
    :param str sep: The separator. Defaults to tab.
    """
    for subj_name, subj_id, subj_resource, rel, obj_name, obj_id, obj_resource in triplets:
        print(subj_name, subj_id, subj_resource, rel, obj_name, obj_id, obj_resource, sep=sep, file=file)
