# -*- coding: utf-8 -*-

"""Utils to generate the D3.js dendrogram. This module is adapted from https://gist.github.com/mdml/7537455"""

import itertools as itt

import pandas as pd
import scipy
import scipy.cluster
import scipy.stats
from scipy.spatial.distance import pdist


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


def label_tree(id_name_dict, name_manager_dict, cluster_to_x, tree):
    if len(tree["children"]) == 0:
        leafs_ids = [tree["node_id"]]

        node_name = id_name_dict[leafs_ids[0]]
        tree["name"] = node_name
        tree["color"] = name_manager_dict[node_name]
        tree["y"] = 0

        return []

    result = [(tree["node_id"], list(tree["children"]))]

    childs = []

    for child in tree["children"]:  # Iterate over the two children
        childs.append(child["node_id"])
        result.extend(label_tree(id_name_dict, name_manager_dict, cluster_to_x, child))  # Recursive tree transversal

    tree["y"] = cluster_to_x[childs[0], childs[1]]

    return result


def get_dendrogram_tree(gene_sets, pathway_manager_dict):
    """Returns json data

    :param dict[str,set[str]] gene_sets: pathway gene sets dict
    :param dict[str,str] pathway_manager_dict: pathway name to manager dictionary
    :rtype: dict
    :return: json tree like structure
    """

    similarity_matrix = create_similarity_matrix(gene_sets)

    # Create the dissimilarity matrix for each row of the similarity matrix using 1-R where R is the pearson correlation
    # Between two rows
    distance_matrix = pdist(similarity_matrix, metric='correlation')

    # Calculate clusters
    clusters = scipy.cluster.hierarchy.linkage(distance_matrix, method='average')
    # Tree lik object
    tree = scipy.cluster.hierarchy.to_tree(clusters, rd=False)

    # Dictionary of tuple of nodes ids (cluster) pointing to the distance in the histogram of that cluster
    cluster_to_x = {
        (int(cluster[0]), int(cluster[1])): cluster[2]
        for cluster in clusters
    }

    # Create dictionaries necessary to label the tree object with node and resource info
    labels = list(similarity_matrix.columns)
    id_name_dict = dict(zip(range(len(labels)), labels))

    # Initialize nested dictionary for d3, then recursively iterate through tree
    d3_dendrogram = dict(children=[], name="Root")
    add_node(tree, d3_dendrogram)

    label_tree(id_name_dict, pathway_manager_dict, cluster_to_x, d3_dendrogram["children"][0])

    import json
    print(json.dumps(d3_dendrogram))

    return d3_dendrogram
