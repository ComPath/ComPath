# -*- coding: utf-8 -*-

"""This module contains all the utils for curation processing."""

from typing import Mapping, Tuple

from bio2bel.compath import CompathManager
from compath.utils import get_pathway_model_by_name


def remove_star_from_pathway_name(pathway_name: str) -> str:
    """Remove the star that label the reference pathway in isPartOf statements."""
    return pathway_name.replace("*", "").strip()


def get_pathways_from_statement(mapping_statement: str, mapping_type: str) -> Tuple[str, str]:
    """Return the subject, object of the mapping.

    :param mapping_statement: statement
    :param mapping_type: type of relationship
    """
    _pathways = mapping_statement.split(mapping_type)
    return _pathways[0].strip(), _pathways[1].strip()


def is_valid_pathway_name(
    manager_dict: Mapping[str, CompathManager],
    resource: str,
    pathway_name: str,
) -> bool:
    """Check if pathway name exists in pathway database.

    :param manager_dict: manager name to manager instances dictionary
    :param resource: resource name
    :param pathway_name: pathway name
    """
    return get_pathway_model_by_name(manager_dict, resource, pathway_name) is not None


def is_valid_pathway_by_id(
    manager_dict: Mapping[str, CompathManager],
    resource: str,
    pathway_id: str,
) -> bool:
    """Check if pathway identifier exists in pathway database.

    :param manager_dict: manager name to manager instances dictionary
    :param resource: resource name
    :param pathway_id: pathway identifier
    """
    return manager_dict[resource].get_pathway_by_id(pathway_id) is not None
