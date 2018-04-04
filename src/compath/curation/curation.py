# -*- coding: utf-8 -*-

"""This module contains all the curation processing scripts to integrate the mappings to ComPath"""

import logging

import pandas as pd

from compath import managers
from compath.constants import MAPPING_TYPES, DEFAULT_CACHE_CONNECTION, IS_PART_OF, EQUIVALENT_TO
from compath.utils import get_pathway_model_by_name

log = logging.getLogger(__name__)


def load_curation_template(path, index_mapping_column=2):
    """Loads the curation template excel sheet into a pandas Dataframe

    :param str path: path of the excel sheet
    :param Optional[int] index_mapping_column: index of the column containing the mappings
    :rtype: pandas.core.series.Series
    :return: pandas.core.series.Series
    """

    data_frame = pd.read_excel(path, header=0, index_col=0)

    return data_frame.iloc[:, index_mapping_column]


def _get_pathways_from_statement(mapping_statement, mapping_type):
    """Returns the subject, object of the mapping

    :param str mapping_statement: statement
    :param str mapping_type: type of relationship
    :rtype: tuple[str,str]
    """

    _pathways = mapping_statement.split(mapping_type)

    return _pathways[0].strip(), _pathways[1].strip()


def _ensure_two_pathways(mapping_statement, mapping_type):
    """Ensures only two pathways are there when splitting the statement

    :param str mapping_statement: statement
    :param str mapping_type: type of relationship
    :rtype: bool
    """

    _pathways = mapping_statement.split(mapping_type)

    if len(_pathways) != 2:
        return False

    return True


def _statement_syntax_checker(mapping_statement, pathway_reference):
    """Checks if a particular mapping contains syntax errors

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
        have_two_pathways = _ensure_two_pathways(mapping_statement, EQUIVALENT_TO)

        if have_two_pathways:
            return True

    if IS_PART_OF in mapping_statement:

        if not "*" in mapping_statement:
            return False

        have_two_pathways = _ensure_two_pathways(mapping_statement, IS_PART_OF)

        if have_two_pathways:
            return True

    return False


def _is_valid_pathway(manager_dict, resource, pathway_name):
    """Checks if pathway exists in pathway database

    :param dict manager_dict: manager name to manager instances dictionary
    :param str resource: resource name
    :param str pathway_name: pathway name
    :rtype: bool
    """

    pathway = get_pathway_model_by_name(manager_dict, resource, pathway_name)

    if not pathway:
        raise ValueError('{} pathway not found'.format(pathway_name))

    return True


def _ensure_syntax(statements):
    """Ensure syntax

    :param pandas.core.series.Series statements: Statements list
    """

    for reference_pathway, cell in statements.iteritems():

        if pd.isnull(cell):
            continue

        for mapping_statement in cell.split('|'):

            if _statement_syntax_checker(mapping_statement, reference_pathway) is False:
                print(
                    'Problem with cell "{}" given the reference pathway: "{}"'.format(mapping_statement,
                                                                                      reference_pathway)
                )


def parse_curation_template(path, index_mapping_column=2):
    """Loads the curation template excel sheet into a pandas Dataframe

    :param str path: path of the excel sheet
    :param Optional[int] index_mapping_column: index of the column containing the mappings
    """

    # Loads the installed managers
    managers_dict = {
        name: ExternalManager(connection=DEFAULT_CACHE_CONNECTION)
        for name, ExternalManager in managers.items()
    }

    mapping_statements = load_curation_template(path)

    # Ensures the Syntax of the file is correct
    _ensure_syntax(mapping_statements)




# Only will open when not imported
if __name__ == '__main__':
    parse_curation_template(
        '/home/ddomingofernandez/Projects/compath/compath_curation/curation/KEGG vs WikiPathways - Daniel.xlsx')
