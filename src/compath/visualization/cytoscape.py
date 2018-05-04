# -*- coding: utf-8 -*-

"""Utils to generate the Cytoscape.js network."""

from collections import defaultdict

from compath.constants import KEGG, KEGG_URL, REACTOME, REACTOME_URL, WIKIPATHWAYS, WIKIPATHWAYS_URL

from networkx import Graph


def mappings_to_cytoscape_js(mappings):
    """ComPath mappings to cytoscape js format

    :param iter mappings:
    :rtype: dict
    """
    graph = mappings_to_networkx(mappings)

    return networkx_to_cytoscape_js(graph)


def mappings_to_networkx(mappings):
    """Create a graph with the mappings relationships

    :param iter mappings:
    :rtype: networkx.graph
    """
    graph = Graph()
    for mapping in mappings:
        graph.add_edge(
            (mapping.service_1_name, mapping.service_1_pathway_id, mapping.service_1_pathway_name),
            (mapping.service_2_name, mapping.service_2_pathway_id, mapping.service_2_pathway_name),
            type=mapping.type
        )

    return graph


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
        node_object["data"]["name"] = node[2]

        if node[0] == REACTOME:
            node_object["data"]["url"] = REACTOME_URL.format(node[2])

        elif node[0] == KEGG:
            node_object["data"]["url"] = KEGG_URL.format(node[2])

        elif node[0] == WIKIPATHWAYS:
            node_object["data"]["url"] = WIKIPATHWAYS_URL.format(node[2])

        network_dict["nodes"].append(node_object.copy())

    for source, target, data in graph.edges(data=True):
        nx = {}
        nx["data"] = {}
        nx["data"]["source"] = info_to_id[source]
        nx["data"]["target"] = info_to_id[target]
        nx["data"]["type"] = data['type']

        network_dict["edges"].append(nx)

    return dict(network_dict)
