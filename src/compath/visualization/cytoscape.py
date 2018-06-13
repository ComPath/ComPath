# -*- coding: utf-8 -*-

"""Utils to generate the Cytoscape.js network."""

import itertools as itt
from collections import defaultdict

from networkx import Graph

from compath.constants import KEGG, KEGG_URL, REACTOME, REACTOME_URL, WIKIPATHWAYS, WIKIPATHWAYS_URL
from compath.utils import calculate_szymkiewicz_simpson_coefficient


def filter_network_by_similarity(graph, min_similarity):
    """Remove edges with similarity less than the minimum given.

    :param networkx.Graph graph: graph
    :param float min_similarity: minimum similarity required to keep an edge
    """

    for source, target, data in graph.edges(data=True):

        if 'similarity' in data and data['similarity'] < min_similarity:
            del graph[source][target]


def pathways_to_similarity_network(manager_dict, pathways):
    """Create a graph with the given pathways related by their similarity

    :param dict manager_dict:
    :param list[tuple(str,str,str)] pathways:
    :rtype: networkx.Graph
    """
    gene_set_dict = {
        identifier: manager_dict[resource].get_pathway_by_id(identifier).get_gene_set()
        for resource, identifier, name in pathways
    }

    graph = Graph()

    for (resource_1, identifier_1, name_1), (resource_2, identifier_2, name_2) in itt.combinations(pathways, r=2):
        similarity = calculate_szymkiewicz_simpson_coefficient(gene_set_dict[identifier_1], gene_set_dict[identifier_2])

        if similarity == 0:
            continue

        graph.add_edge(
            (resource_1, identifier_1, name_1),
            (resource_2, identifier_2, name_2),
            similarity=similarity
        )

    return graph


def enrich_graph_with_mappings(graph, mappings):
    """Enrich a graph with the mapping information.

    :param graph networkx.Graph:
    :param iter mappings:
    """
    for mapping in mappings:
        graph.add_edge(
            (mapping.service_1_name, mapping.service_1_pathway_id, mapping.service_1_pathway_name),
            (mapping.service_2_name, mapping.service_2_pathway_id, mapping.service_2_pathway_name),
            type=mapping.type
        )


def networkx_to_cytoscape_js(graph):
    """Convert a networkx graph to the cytoscape json format.

    :param iter[PathwayMapping] graph:
    :rtype: dict
    """
    network_dict = defaultdict(list)

    info_to_id = {}  # linking pathway info tuple to identifier

    for node_id, node in enumerate(graph.nodes()):

        info_to_id[node] = node_id

        node_object = {}
        node_object["data"] = {}
        node_object["data"]["id"] = node_id
        node_object["data"]["resource"] = node[0]
        node_object["data"]["resource_id"] = node[1]

        if node[0] == 'kegg':
            node_object["data"]["name"] = node[2].replace(" - Homo sapiens (human)", "")
        else:
            node_object["data"]["name"] = node[2]

        if node[0] == REACTOME:
            node_object["data"]["url"] = REACTOME_URL.format(node[1])

        elif node[0] == KEGG:
            node_object["data"]["url"] = KEGG_URL.format(node[1].strip('path:hsa'))

        elif node[0] == WIKIPATHWAYS:
            node_object["data"]["url"] = WIKIPATHWAYS_URL.format(node[1])

        network_dict["nodes"].append(node_object.copy())

    for source, target, data in graph.edges(data=True):
        nx = {}
        nx["data"] = {}
        nx["data"]["source"] = info_to_id[source]
        nx["data"]["target"] = info_to_id[target]

        if 'type' in data:
            nx["data"]["type"] = data['type']

        if 'similarity' in data:
            nx["data"]["similarity"] = data['similarity']

        network_dict["edges"].append(nx)

    return dict(network_dict)
