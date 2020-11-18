# -*- coding: utf-8 -*-

"""Utils to generate the Cytoscape.js network."""

from typing import Any, Iterable, List, Mapping, Tuple

import itertools as itt
import networkx as nx

from bio2bel.compath import CompathManager
from ..models import PathwayMapping
from ..utils import calculate_szymkiewicz_simpson_coefficient


def filter_network_by_similarity(graph: nx.Graph, min_similarity: float) -> None:
    """Remove edges with similarity less than the minimum given.

    :param graph: graph
    :param min_similarity: minimum similarity required to keep an edge
    """
    for source, target, data in graph.edges(data=True):
        if 'similarity' in data and data['similarity'] < min_similarity:
            del graph[source][target]


def pathways_to_similarity_network(
    managers: Mapping[str, CompathManager],
    pathways: List[Tuple[str, str, str]],
) -> nx.Graph:
    """Create a graph with the given pathways related by their similarity."""
    gene_set_dict = {
        identifier: managers[prefix].get_pathway_by_id(identifier).get_hgnc_symbols()
        for prefix, identifier, name in pathways
    }

    graph = nx.Graph()

    for (prefix_1, identifier_1, name_1), (prefix_2, identifier_2, name_2) in itt.combinations(pathways, r=2):
        similarity = calculate_szymkiewicz_simpson_coefficient(
            gene_set_dict[identifier_1],
            gene_set_dict[identifier_2],
        )

        if similarity == 0:
            continue

        graph.add_edge(
            (prefix_1, identifier_1, name_1),
            (prefix_2, identifier_2, name_2),
            similarity=similarity,
        )

    return graph


def enrich_graph_with_mappings(graph: nx.Graph, mappings: Iterable[PathwayMapping]) -> None:
    """Enrich a graph with the mapping information."""
    for mapping in mappings:
        graph.add_edge(
            (mapping.service_1_name, mapping.service_1_pathway_id, mapping.service_1_pathway_name),
            (mapping.service_2_name, mapping.service_2_pathway_id, mapping.service_2_pathway_name),
            type=mapping.type,
        )


def networkx_to_cytoscape_js(graph: nx.Graph) -> Mapping[str, List[Any]]:
    """Convert a networkx graph to the cytoscape json format."""
    nodes = []
    info_to_id = {}
    for i, (prefix, identifier, name) in enumerate(sorted(graph)):
        info_to_id[prefix, identifier, name] = i
        nodes.append({
            "data": {
                'id': i,
                'prefix': prefix,
                'identifier': identifier,
                'name': name,
                'url': f'https://identifiers.org/{prefix}:{identifier}',
            },
        })

    edges = []
    for source, target, data in graph.edges(data=True):
        edge = {
            "data": {
                'source': info_to_id[source],
                'target': info_to_id[target],
            },
        }
        if 'type' in data:
            edge["data"]["type"] = data['type']
        if 'similarity' in data:
            edge["data"]["similarity"] = data['similarity']

        edges.append(edge)

    return {'nodes': nodes, 'edges': edges}
