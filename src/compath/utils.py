# -*- coding: utf-8 -*-

"""This module contains miscellaneous methods."""

import logging
from collections import defaultdict
from difflib import SequenceMatcher
from itertools import combinations
from operator import itemgetter
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple

import numpy as np
from pandas import DataFrame, Series
from scipy.stats import fisher_exact
from sqlalchemy import and_
from statsmodels.sandbox.stats.multicomp import multipletests

from bio2bel.compath import CompathManager, CompathPathwayMixin
from bio2bel.models import Action, _make_session
from .constants import BLACKLIST
from .models import User

logger = logging.getLogger(__name__)

"""General utils"""


# modified from https://stackoverflow.com/questions/19736080/creating-dataframe-from-a-dictionary-where-entries-have-different-lengths

def dict_to_pandas_df(d: Mapping[str, Iterable[str]]):
    """Transform pandas df into a dict.

    :param dict d:
    :rtype: pandas.DataFrame
    :return: pandas dataframe
    """
    return DataFrame({
        k: Series(list(v))
        for k, v in d.items()
    })


def process_form_gene_set(text: str) -> Set[str]:
    """Process the string containing gene symbols and returns a gene set.

    :param text: string to be processed
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


def calculate_relative_enrichments(
    resource_to_enriched_pathways: Mapping[str, List[str]],
    total_pathways_by_resource: Mapping[str, int],
) -> Mapping[str, float]:
    """Calculate relative enrichment of pathways (enriched pathways/total pathways).

    :param dict resource_to_enriched_pathways: result enrichment
    :param dict total_pathways_by_resource: resource to number of pathways
    :rtype: dict
    """
    rv = {}
    for resource, pathways in resource_to_enriched_pathways.items():
        n_enriched_pathways = len(pathways)
        denom = total_pathways_by_resource[resource]
        rv[resource] = n_enriched_pathways / denom
    return rv


def count_genes_in_pathways(
    pathways: Mapping[str, Set[str]],
    query: Set[str],
) -> Mapping[str, int]:
    """Calculate how many of the genes are associated to each pathway gene set.

    :param pathways: pathways and their gene sets
    :param query: Set of HGNC gene symbols to be queried queried
    """
    return {
        pathway: len(gene_set.intersection(query))
        for pathway, gene_set in pathways.items()
    }


def apply_filter(
    resource_to_pathway_to_hit_count: Mapping[str, Mapping[str, int]],
    threshold: int,
) -> Mapping[str, List[str]]:
    """Run one simulation with a given threshold.

    :param resource_to_pathway_to_hit_count: resource with pathways
    :param threshold: necessary genes to enrich a pathway
    :rtype: dict
    """
    filtered_results = defaultdict(list)

    for database_name, pathways in resource_to_pathway_to_hit_count.items():
        for pathway_name, genes_mapped in pathways.items():
            if genes_mapped < threshold:
                continue
            filtered_results[database_name].append(pathway_name)

    return filtered_results


def simulate_pathway_enrichment(
    resource_pathways: Mapping[str, Mapping[str, Set[str]]],
    query: Set[str],
    runs: int = 200,
) -> Mapping[str, List[float]]:
    """Simulate pathway enrichment.

    :param resource_pathways: resource and their gene sets
    :param query: shared genes between all resources
    :param runs: number of simulation
    :rtype: dict[list[tuple]]
    """
    # How many pathways each resource (Database) has
    resource_to_pathway_count: Mapping[str, int] = {
        resource: len(pathways)
        for resource, pathways in resource_pathways.items()
    }

    # How many genes of the 'gene_set_query' are in each pathway
    resource_to_pathway_to_hit_count: Mapping[str, Mapping[str, int]] = {
        resource: count_genes_in_pathways(pathways, query)
        for resource, pathways in resource_pathways.items()
    }

    results: Dict[str, List[float]] = defaultdict(list)

    # Calculate the percentage of pathways in the database with a minimum of genes in the pathway
    for threshold in range(1, runs):
        filtered_results: Mapping[str, List[str]] = apply_filter(resource_to_pathway_to_hit_count, threshold)

        relative_enrichments: Mapping[str, float] = calculate_relative_enrichments(
            filtered_results,
            resource_to_pathway_count,
        )

        for resource, result in relative_enrichments.items():
            results[resource].append(round(result, 3))

    return dict(results)


"""Query utils"""


def _iterate_user_strings(manager_):
    """Iterate over strings to print describing users.

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
    """Return the genes without any known pathway assigned.

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


def get_enriched_pathways(managers: Mapping[str, CompathManager], hgnc_symbols: Set[str]):
    """Return the results of the queries for every registered manager.

    :param managers: list of managers
    :param hgnc_symbols: gene set queried
    :rtype: dict[str,dict[str,dict]]
    """
    return {
        prefix: manager.query_hgnc_symbols(hgnc_symbols)
        for prefix, manager in managers.items()
        if prefix not in BLACKLIST
    }


def get_gene_pathways(managers: Mapping[str, CompathManager], hgnc_symbol: str):
    """Return the pathways associated with a gene for every registered manager.

    :param managers: list of managers
    :param hgnc_symbol: HGNC symbol
    :rtype: dict[str,dict[str,dict]]
    """
    return {
        prefix: manager.query_hgnc_symbol(hgnc_symbol)
        for prefix, manager in managers.items()
        if prefix not in BLACKLIST
    }


def get_pathway_model_by_name(
    manager_dict: Mapping[str, CompathManager],
    resource: str,
    pathway_name: str,
) -> Optional[CompathPathwayMixin]:
    """Return the pathway object from the resource manager.

    :param manager_dict: manager name to manager instances dictionary
    :param resource: name of the manager
    :param pathway_name: pathway name
    """
    manager: CompathManager = manager_dict[resource.lower()]
    return manager.get_pathway_by_name(pathway_name)


def get_last_action_in_module(module_name: str, action: str, session=None):
    """Return the info about the last action in the given module."""
    if session is None:
        session = _make_session()
    _filter = and_(Action.resource == module_name, Action.action == action)
    return session.query(Action).filter(_filter).order_by(Action.created.desc()).first()


"""Statistical utils"""


def _prepare_hypergeometric_test(query_gene_set, pathway_gene_set, gene_universe):
    """Prepare the matrix for hypergeometric test calculations.

    :param set[str] query_gene_set: gene set to test against pathway
    :param set[str] pathway_gene_set: pathway gene set
    :param int gene_universe: number of HGNC symbols
    :rtype: numpy.ndarray
    :return: 2x2 matrix
    """
    return np.array([
        [
            len(query_gene_set.intersection(pathway_gene_set)),
            len(query_gene_set.difference(pathway_gene_set)),
        ],
        [
            len(pathway_gene_set.difference(query_gene_set)),
            gene_universe - len(pathway_gene_set.union(query_gene_set)),
        ],
    ])


def perform_hypergeometric_test(
    gene_set,
    manager_pathways_dict,
    gene_universe,
    apply_threshold=False,
    threshold=0.05,
):
    """Perform hypergeometric tests.

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


def calculate_similarity(a: str, b: str) -> float:
    """Calculate the string based similarity between two names.

    :return: Levenshtein similarity
    """
    return SequenceMatcher(None, a, b).ratio()


def get_top_matches(matches: List[Tuple], top: int) -> List[Tuple]:
    """Order list of tuples by second value and returns top values.

    :param matches: list of tuples
    :param top: top values to return
    """
    sorted_names = sorted(matches, key=itemgetter(1), reverse=True)
    return sorted_names[:top]


def get_most_similar_names(
    query: str,
    entities: Iterable[Tuple[str, str, str]],
    threshold: float = 0.4,
    top: int = 5,
) -> List[Tuple[str, str, str, float]]:
    """Return the most similar names based on string matching.

    :param query:
    :param entities:
    :param threshold:
    :param top:
    :return:
    """
    string_matching = (
        (prefix, identifier, name, calculate_similarity(query, name))
        for prefix, identifier, name in entities
    )
    most_similar_names = (
        (prefix, identifier, name, similarity)
        for prefix, identifier, name, similarity in string_matching
        if similarity >= threshold
    )
    # FIXME better algorithm for picking top N
    most_similar_names = sorted(most_similar_names, key=itemgetter(3), reverse=True)
    return most_similar_names[:top]


"""Export utils"""


def to_csv(triplets, file=None, sep='\t'):
    """Writs triplets as a tab-separated.

    :param iterable[tuple[str,str,str]] triplets: iterable of triplets
    :param file file: A writable file or file-like. Defaults to stdout.
    :param str sep: The separator. Defaults to tab.
    """
    for subj_name, subj_id, subj_resource, rel, obj_name, obj_id, obj_resource in triplets:
        print(subj_name, subj_id, subj_resource, rel, obj_name, obj_id, obj_resource, sep=sep, file=file)


def process_overlap_for_venn_diagram(
    gene_sets: Mapping[str, Set[str]],
    skip_gene_set_info: bool = False,
) -> List[Mapping[str, Any]]:
    """Calculate gene sets overlaps and process the structure to render venn diagram -> https://github.com/benfred/venn.js/.

    :param gene_sets: pathway to gene sets dictionary
    :param skip_gene_set_info: include gene set overlap data
    """
    # Creates future js array with gene sets' lengths
    overlaps_venn_diagram = []

    pathway_to_index = {}
    for index, (name, gene_set) in enumerate(gene_sets.items()):
        av = {
            'sets': [index],
            'size': len(gene_set),
            'label': name.upper(),
        }
        if not skip_gene_set_info:
            av['gene_set'] = list(gene_set)
        overlaps_venn_diagram.append(av)
        pathway_to_index[name] = index

    # Perform intersection calculations
    for (set_1_name, set_1_values), (set_2_name, set_2_values) in combinations(gene_sets.items(), r=2):
        # Only minimum info is returned
        if skip_gene_set_info:
            overlaps_venn_diagram.append({
                'sets': [pathway_to_index[set_1_name], pathway_to_index[set_2_name]],
                'size': len(set_1_values.intersection(set_2_values)),
            })
        # Returns gene set overlap/intersection information as well
        else:
            overlaps_venn_diagram.append({
                'sets': [pathway_to_index[set_1_name], pathway_to_index[set_2_name]],
                'size': len(set_1_values.intersection(set_2_values)),
                'gene_set': list(set_1_values.intersection(set_2_values)),
                'intersection': set_1_name + ' &#8745 ' + set_2_name,
            })

    return overlaps_venn_diagram
