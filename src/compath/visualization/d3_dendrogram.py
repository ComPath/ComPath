# -*- coding: utf-8 -*-

"""Utils to generate the D3.js dendrogram. This module is adapted from https://gist.github.com/mdml/7537455."""

import itertools as itt
import math

import numpy as np
import pandas as pd
import scipy
import scipy.cluster
import scipy.stats
from scipy.spatial.distance import pdist


def _check_error_distance(distance_matrix, pathway_manager_dict, similarity_matrix):
    """Remove column and row in matrix after value error to proceed with clustering.

    :param numpy.ndarray distance_matrix:
    :param dict pathway_manager_dict:
    :param pandas.DataFrame similarity_matrix:
    :rtype: tuple(numpy.ndarray, dict, pandas.DataFrame)
    :return: distance matrix, pathway_manager_dict, and similarity_matrix
    """
    if np.all(np.isfinite(distance_matrix)):
        return distance_matrix, pathway_manager_dict, similarity_matrix

    # Checks rows that only contain one unique number and this number is close to 1
    pathways_to_remove = {
        index
        for index, row in similarity_matrix.iterrows()
        if row.nunique() == 1 and math.isclose(row.unique()[0], 1, rel_tol=1e-5)
    }

    # Remove all columns/rows having the pathway label
    for pathway in pathways_to_remove:
        similarity_matrix = similarity_matrix.drop(axis=0, labels=pathway)
        similarity_matrix = similarity_matrix.drop(axis=1, labels=pathway)

    # Recalculate the distances
    distance_matrix = pdist(
        similarity_matrix,
        metric='correlation',
        # **{'centered': False} # TODO: try in Python 3.6
    )

    # Remove pathways
    for pathway in pathways_to_remove:
        pathway_manager_dict.pop(pathway)

    return distance_matrix, pathway_manager_dict, similarity_matrix


def create_similarity_matrix(gene_sets):
    """Create a similarity matrix for a given pathway-geneset dataset.

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
    """Create a nested dictionary from the ClusterNode's returned by SciPy.

    :param node:
    :param dict parent:
    """
    # First create the new node and append it to its parent's children
    new_node = dict(node_id=node.id, children=[])
    parent["children"].append(new_node)

    # Recursively add the current node's children
    if node.left:
        add_node(node.left, new_node)
    if node.right:
        add_node(node.right, new_node)


def label_tree(id_name_dict, name_manager_dict, cluster_to_x, tree):
    """Label the tree in a recursive way with names, resource and cluster information.

    :param dict[str,str] id_name_dict: node_id to name dictionary
    :param dict[str,str] name_manager_dict: node name to resource ditionary
    :param dict[tuple[int,int],float] cluster_to_x: node_id tuple of the cluster to distance
    :param dict tree: tree like structure
    :rtype: list
    """
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
    """Return ready to plot json data.

    :param dict[str,set[str]] gene_sets: pathway gene sets dict
    :param dict[str,str] pathway_manager_dict: pathway name to manager dictionary
    :rtype: tuple[dict,int]
    :return: json tree like structure
    """
    similarity_matrix = create_similarity_matrix(gene_sets)

    # Create the dissimilarity matrix for each row of the similarity matrix using 1-R where R is the pearson correlation
    # Between two rows
    distance_matrix = pdist(
        similarity_matrix,
        metric='correlation',
        # **{'centered': False} # TODO: try in Python 3.6
    )

    # Checks for exceptions (pathways with 1 gene only matching the gene queried causes division by zero problems because the distance of this pathway to all others is 1.0)
    distance_matrix, pathway_manager_dict, similarity_matrix = _check_error_distance(
        distance_matrix,
        pathway_manager_dict,
        similarity_matrix
    )

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
    pathways = list(similarity_matrix.columns)
    id_name_dict = dict(zip(range(len(pathways)), pathways))

    # Initialize nested dictionary for d3, then recursively iterate through tree
    d3_dendrogram = dict(children=[], name="Root")
    add_node(tree, d3_dendrogram)

    label_tree(id_name_dict, pathway_manager_dict, cluster_to_x, d3_dendrogram["children"][0])

    return d3_dendrogram, len(pathways)


def get_descendants(manager, resource, pathway_id, pathway_name):
    """Generate d3 dendrogram structure by using BFS starting from the starting from a parent (root) node to the last descendants.

    :param manager: ComPath manager
    :param str resource: resource name
    :param str pathway_id: pathway identifier in the resource
    :param str pathway_name: pathway name
    :return: parent-children data structure
    :rtype: list[dict]
    """
    # Create the entry dictionary of the pathway (node).
    d3_dendrogram = dict(
        children=[],
        name=pathway_name.replace(' - Homo sapiens (human)', ''),  # Replace KEGG Suffixes
        pathway_id=pathway_id,
        resource=resource
    )

    # Get direct descendents for the pathway.
    descendent_mappings = manager.get_decendents_mappings_from_pathway_with_is_part_of_relationship(
        resource,
        pathway_id,
        pathway_name
    )

    # Return the entry dict with no children if the node got no descendants.
    if not descendent_mappings:
        return d3_dendrogram

    # Do the recusive call for each child.
    for mapping in descendent_mappings:
        pathway = mapping.get_complement_mapping_info(resource, pathway_id, pathway_name)

        d3_dendrogram["children"].append(
            get_descendants(
                manager,
                pathway[0],
                pathway[1],
                pathway[2]
            )
        )

    return d3_dendrogram


def get_mapping_dendrogram(manager, resource, pathway_id, pathway_name):
    """Generate d3 dendrogram structure by using BFS starting from the queried node in both directions of the hierarchy.

    :param manager: ComPath manager
    :param str resource: resource name
    :param str pathway_id: pathway identifier in the resource
    :param str pathway_name: pathway name
    :return: parent-children data structure
    :rtype: list[dict]
    """
    ancestries_mappings = []
    common_ancestries = []
    root = [resource, pathway_id, pathway_name]

    # Get direct progenitors for the pathway.
    ancestry_mappings = manager.get_ancestry_mappings_from_pathway_with_is_part_of_relationship(
        resource,
        pathway_id,
        pathway_name
    )

    # Set as root if there is some progenitor (parent)
    if ancestry_mappings:
        root = ancestry_mappings[0].get_complement_mapping_info(resource, pathway_id, pathway_name)

    # If there are many progenitors, get the common ancestry of the progenitors (parents)
    if len(ancestry_mappings) > 1:
        for ancestry in ancestry_mappings:
            pathway = ancestry.get_complement_mapping_info(resource, pathway_id, pathway_name)
            mapping = manager.get_ancestry_mappings_from_pathway_with_is_part_of_relationship(
                pathway[0],
                pathway[1],
                pathway[2]
            )
            if mapping:
                ancestries_mappings.append(mapping)
                if not common_ancestries:
                    common_ancestries = set(mapping)
                else:
                    common_ancestries.intersection(set(mapping))

    # Set as root if there is some ancestry (grandparent)
    if common_ancestries:
        root = list(common_ancestries)[0].get_complement_mapping_info(resource, pathway_id, pathway_name)

    # If there are many ancestries, do a recursive call to get the ancestries (grandparents)
    if len(common_ancestries) > 1:
        get_mapping_dendrogram(
            manager,
            root[0],
            root[1],
            root[2]
        )

    return get_descendants(manager, root[0], root[1], root[2])


def add_mapping_node(id_name_dict, name_manager_dict, cluster_to_x, tree):
    """Label the tree in a recursive way with names, resource and cluster information.

    :param dict[str,str] id_name_dict: node_id to name dictionary
    :param dict[str,str] name_manager_dict: node name to resource ditionary
    :param dict[tuple[int,int],float] cluster_to_x: node_id tuple of the cluster to distance
    :param dict tree: tree like structure
    :rtype: list
    """
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
