# -*- coding: utf-8 -*-

"""Utils to generate the D3.js dendrogram. This module is modified from https://gist.github.com/mdml/7537455"""

import pandas as pd
import itertools as itt
import scipy.cluster
from functools import reduce


def create_similarity_matrix(gene_sets):
    """Creates a similarity matrix for a given pathway-geneset dataset

    :param dict gene_sets: pathway gene set dictionary
    :rtype: pandas.DataFrame
    :returns: similarity matrix
    """

    index = sorted(gene_sets.keys())
    similarity_dataframe = pd.DataFrame(0.0, index=index, columns=index)

    for pathway_1, pathway_2 in itt.product(index, index):
        intersection = len(gene_sets[pathway_1].intersection(gene_sets[pathway_2]))
        smaller_set = min(len(gene_sets[pathway_1]), len(gene_sets[pathway_2]))

        similarity = float(intersection / smaller_set)  # Formula to calculate similarity

        similarity_dataframe[pathway_1][pathway_2] = similarity

    return similarity_dataframe


def add_node(node, parent):
    """Create a nested dictionary from the ClusterNode's returned by SciPy

    :param node:
    :param dict parent:
    """
    # First create the new node and append it to its parent's children
    newNode = dict(node_id=node.id, children=[])
    parent["children"].append(newNode)

    # Recursively add the current node's children
    if node.left: add_node(node.left, newNode)
    if node.right: add_node(node.right, newNode)


def label_tree(id2name, name2manager, n):
    """Labels each node with the names of each leaf in its subtree

    :param dict id2name: column id to name dictionary
    :param dict name2manager: name to pathway db dictionary
    :param n: tree
    :type: list
    """
    # If the node is a leaf, then we have its name
    if len(n["children"]) == 0:
        leafNames = [id2name[n["node_id"]]]

    # If not, flatten all the leaves in the node's subtree
    else:
        leafNames = reduce(lambda ls, c: ls + label_tree(id2name, c), n["children"], [])

    # Delete the node id since we don't need it anymore and
    # it makes for cleaner JSON
    del n["node_id"]

    # Labeling convention: "-"-separated leaf names
    n["name"] = name = "-".join(sorted(map(str, leafNames)))
    n["color"] = name2manager[name]

    return leafNames


def get_dendrogram_tree(gene_sets, pathway_manager_dict):
    """Returns json data

    :param dict[str,set[str]] gene_sets: pathway gene sets dict
    :param dict[str,str] pathway_manager_dict: pathway name to manager dictionary
    :rtype: dict
    :return: json tree like structure
    """

    similarity_matrix = create_similarity_matrix(gene_sets)

    # Cluster hierarchicaly using scipy
    clusters = scipy.cluster.hierarchy.linkage(similarity_matrix, method='single')
    tree = scipy.cluster.hierarchy.to_tree(clusters, rd=False)

    # Create dictionary for labeling nodes by their IDs
    labels = list(similarity_matrix.columns)
    id2name = dict(zip(range(len(labels)), labels))

    # Initialize nested dictionary for d3, then recursively iterate through tree
    d3Dendro = dict(children=[], name="Root")
    add_node(tree, d3Dendro)

    label_tree(id2name, pathway_manager_dict, d3Dendro["children"][0])

    return d3Dendro
