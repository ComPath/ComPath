# -*- coding: utf-8 -*-

"""This module contains all the utils for curation processing."""

from compath.utils import get_pathway_model_by_id, get_pathway_model_by_name


def remove_star_from_pathway_name(pathway_name):
    """Remove the star that label the reference pathway in isPartOf statements.

    :param str statements: pathway name
    """
    return pathway_name.replace("*", "").strip()


def get_pathways_from_statement(mapping_statement, mapping_type):
    """Return the subject, object of the mapping.

    :param str mapping_statement: statement
    :param str mapping_type: type of relationship
    :rtype: tuple[str,str]
    """
    _pathways = mapping_statement.split(mapping_type)

    return _pathways[0].strip(), _pathways[1].strip()


def is_valid_pathway_name(manager_dict, resource, pathway_name):
    """Check if pathway name exists in pathway database.

    :param dict manager_dict: manager name to manager instances dictionary
    :param str resource: resource name
    :param str pathway_name: pathway name
    :rtype: bool
    """
    pathway = get_pathway_model_by_name(manager_dict, resource, pathway_name)

    if not pathway:
        return False

    return True


def is_valid_pathway_by_id(manager_dict, resource, pathway_id):
    """Check if pathway identifier exists in pathway database.

    :param dict manager_dict: manager name to manager instances dictionary
    :param str resource: resource name
    :param str pathway_id: pathway identifier
    :rtype: bool
    """
    pathway = manager_dict[resource].get_pathway_by_id(pathway_id)

    if not pathway:
        return False

    return True
