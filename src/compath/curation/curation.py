# -*- coding: utf-8 -*-

"""This module contains all the curation processing scripts to integrate the mappings to ComPath"""

import logging

import pandas as pd

from compath import managers
from compath.constants import MAPPING_TYPES, DEFAULT_CACHE_CONNECTION, IS_PART_OF, EQUIVALENT_TO, ADMIN_EMAIL
from compath.manager import RealManager
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


def _get_mapping_type(mapping_statement):
    """Returns the mapping type from a given statement

    :param str mapping_statement:
    :rtype: Optional[str]
    """

    if EQUIVALENT_TO in mapping_statement:
        return EQUIVALENT_TO

    elif IS_PART_OF in mapping_statement:
        return IS_PART_OF

    return None


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
        return False

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


def _remove_star_from_pathway_name(pathway_name):
    """Removes the star that label the reference pathway in isPartOf statements

    :param str statements: pathway name
    """
    return pathway_name.replace("*", "").strip()


def parse_curation_template(path, reference_pathway_db, compared_pathway_db, index_mapping_column=2, admin_email=None):
    """Loads the curation template excel sheet into a pandas Dataframe

    :param str path: path of the excel sheet
    :param str reference_pathway_db: name of the manager of the reference pathway_db
    :param str compared_pathway_db: name of the manager of the compared pathway_db
    :param Optional[int] index_mapping_column: index of the column containing the mappings
    :param str admin_email: email of the admin. Needs to be already in the database
    """

    # Loads the installed managers
    manager_dict = {
        name: ExternalManager(connection=DEFAULT_CACHE_CONNECTION)
        for name, ExternalManager in managers.items()
    }

    mapping_statements = load_curation_template(path, index_mapping_column=index_mapping_column)

    # Ensures the Syntax of the file is correct
    _ensure_syntax(mapping_statements)

    compath_manager = RealManager()

    curator = compath_manager.get_user_by_email(email=admin_email if admin_email else ADMIN_EMAIL)

    if not curator:
        raise EnvironmentError(
            'There is no user with the email "{}". Please create it with the "make_user" command using '
            'the command line interface of Compath'
        )

    # Populate the curated mappings
    for reference_pathway, mapping_statement in mapping_statements.iteritems():
        mapping_type = _get_mapping_type(mapping_statement)

        if not mapping_type:
            raise ValueError(
                'Problem with mapping type in "{}" given the reference pathway: "{}"'.format(
                    mapping_statement,
                    reference_pathway)
            )

        pathway_1, pathway_2 = _get_pathways_from_statement(mapping_statement, mapping_type)

        if mapping_type == IS_PART_OF:

            if "*" in pathway_1:

                # Ensures the pathways exist in their corresponding managers
                if _is_valid_pathway(manager_dict, reference_pathway_db, pathway_1) is False:
                    raise ValueError('{} not found in {}'.format(pathway_1, reference_pathway_db))

                if _is_valid_pathway(manager_dict, compared_pathway_db, pathway_2) is False:
                    raise ValueError('{} not found in {}'.format(pathway_2, compared_pathway_db))

                pathway_1 = _remove_star_from_pathway_name(pathway_1)

                mapping, _ = compath_manager.get_or_create_mapping(
                    reference_pathway_db,
                    manager_dict[reference_pathway_db].get_pathway_by_name(pathway_1).id,
                    pathway_1,
                    compared_pathway_db,
                    manager_dict[compared_pathway_db].get_pathway_by_name(pathway_2).id,
                    pathway_2,
                    IS_PART_OF,
                    curator
                )

                mapping, _ = compath_manager.accept_mapping(mapping.id)

            else:

                # Ensures the pathways exist in their corresponding managers
                if _is_valid_pathway(manager_dict, compared_pathway_db, pathway_1) is False:
                    raise ValueError('{} not found in {}'.format(pathway_1, reference_pathway_db))

                if _is_valid_pathway(manager_dict, reference_pathway_db, pathway_2) is False:
                    raise ValueError('{} not found in {}'.format(pathway_2, compared_pathway_db))

                pathway_2 = _remove_star_from_pathway_name(pathway_2)

                mapping, _ = compath_manager.get_or_create_mapping(
                    compared_pathway_db,
                    manager_dict[compared_pathway_db].get_pathway_by_name(pathway_2).id,
                    pathway_2,
                    reference_pathway_db,
                    manager_dict[reference_pathway_db].get_pathway_by_name(pathway_1).id,
                    pathway_1,
                    IS_PART_OF,
                    curator
                )

                mapping, _ = compath_manager.accept_mapping(mapping.id)


        else:  # EquivalentTo

            # Ensures the pathways exist in their corresponding managers
            if _is_valid_pathway(manager_dict, reference_pathway_db, pathway_1) is False:
                raise ValueError('{} not found in {}'.format(pathway_1, reference_pathway_db))

            if _is_valid_pathway(manager_dict, compared_pathway_db, pathway_2) is False:
                raise ValueError('{} not found in {}'.format(pathway_2, compared_pathway_db))

            mapping, _ = compath_manager.get_or_create_mapping(
                reference_pathway_db,
                manager_dict[reference_pathway_db].get_pathway_by_name(pathway_1).id,
                pathway_1,
                compared_pathway_db,
                manager_dict[compared_pathway_db].get_pathway_by_name(pathway_2).id,
                pathway_2,
                EQUIVALENT_TO,
                curator
            )

            mapping, _ = compath_manager.accept_mapping(mapping.id)


# Only will open when not imported
if __name__ == '__main__':
    parse_curation_template(
        '/home/ddomingofernandez/Projects/compath/compath_curation/curation/KEGG vs WikiPathways - Daniel.xlsx', 'kegg',
        'wikipathways')
