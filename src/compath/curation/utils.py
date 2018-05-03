# -*- coding: utf-8 -*-

"""This module contains all the utils for curation processing."""

import pandas as pd

from compath.constants import *
from compath.utils import get_pathway_model_by_name


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


def ensure_two_pathways(mapping_statement, mapping_type):
    """Ensure that only two pathways are there when splitting the statement.

    :param str mapping_statement: statement
    :param str mapping_type: type of relationship
    :rtype: bool
    """
    _pathways = mapping_statement.split(mapping_type)

    if len(_pathways) != 2:
        return False

    return True


def load_curation_template(path, index_mapping_column=2):
    """Loads the curation template excel sheet into a pandas Dataframe

    :param str path: path of the excel sheet
    :param Optional[int] index_mapping_column: index of the column containing the mappings
    :rtype: pandas.core.series.Series
    :return: pathways with mappings
    """
    data_frame = pd.read_excel(path, header=0, index_col=0)

    mapping_statements = data_frame.iloc[:, index_mapping_column]

    return mapping_statements.dropna()


def get_mapping_type(mapping_statement):
    """Return the mapping type from a given statement

    :param str mapping_statement:
    :rtype: Optional[str]
    """
    if EQUIVALENT_TO in mapping_statement:
        return EQUIVALENT_TO

    elif IS_PART_OF in mapping_statement:
        return IS_PART_OF

    return None


def statement_syntax_checker(mapping_statement, pathway_reference):
    """Check if a particular mapping contains syntax errors.

    :param str mapping_statement: mapping statement
    :param str pathway_reference: name of the pathway of reference
    :rtype: bool
    """
    # Checks type
    if not isinstance(mapping_statement, str):
        return False

    # Checks the the statement contain a valid mapping type
    if pathway_reference not in mapping_statement or not any(
            mapping_type in mapping_statement for mapping_type in MAPPING_TYPES):
        return False

    mapping_statement = mapping_statement.strip()

    # Handling mapping types
    if EQUIVALENT_TO in mapping_statement and mapping_statement.startswith(pathway_reference):
        have_two_pathways = ensure_two_pathways(mapping_statement, EQUIVALENT_TO)

        if have_two_pathways:
            return True

    if IS_PART_OF in mapping_statement:

        if not "*" in mapping_statement:
            return False

        have_two_pathways = ensure_two_pathways(mapping_statement, IS_PART_OF)

        if have_two_pathways:
            return True

    return False


def is_valid_pathway(manager_dict, resource, pathway_name):
    """Check if pathway exists in pathway database.

    :param dict manager_dict: manager name to manager instances dictionary
    :param str resource: resource name
    :param str pathway_name: pathway name
    :rtype: bool
    """
    pathway = get_pathway_model_by_name(manager_dict, resource, pathway_name)

    if not pathway:
        return False

    return True


def ensure_syntax(statements):
    """Ensure syntax.

    :param pandas.core.series.Series statements: Statements list
    """
    for reference_pathway, cell in statements.iteritems():

        for mapping_statement in cell.split('|'):

            if statement_syntax_checker(mapping_statement, reference_pathway) is False:
                print(
                    'Problem with cell "{}" given the reference pathway: "{}"'.format(
                        mapping_statement,
                        reference_pathway)
                )
