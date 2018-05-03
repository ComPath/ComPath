# -*- coding: utf-8 -*-

"""This module contains all the curation processing methods to integrate curated mappings to ComPath."""

import logging

from compath import managers
from compath.curation.utils import *
from compath.manager import RealManager

log = logging.getLogger(__name__)


def parse_curation_template(path, reference_pathway_db, compared_pathway_db, index_mapping_column=2, admin_email=None):
    """Load the curation template excel sheet into a pandas Dataframe.

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
    ensure_syntax(mapping_statements)

    compath_manager = RealManager()

    curator = compath_manager.get_user_by_email(email=admin_email if admin_email else ADMIN_EMAIL)

    if not curator:
        raise EnvironmentError(
            'There is no user with the email "{}". Please create it with the "make_user" command using '
            'the command line interface of Compath'
        )

    # Populate the curated mappings
    for reference_pathway, cell in mapping_statements.items():

        for mapping_statement in cell.split('|'):

            mapping_type = get_mapping_type(mapping_statement)

            if not mapping_type:
                raise ValueError(
                    'Problem with mapping type in "{}" given the reference pathway: "{}"'.format(
                        mapping_statement,
                        reference_pathway)
                )

            pathway_1, pathway_2 = get_pathways_from_statement(mapping_statement, mapping_type)

            if mapping_type == IS_PART_OF:

                if "*" in pathway_1:

                    pathway_1 = remove_star_from_pathway_name(pathway_1)

                    # Ensures the pathways exist in their corresponding managers
                    if is_valid_pathway(manager_dict, reference_pathway_db, pathway_1) is False:
                        log.error(
                            '"{}" not found in "{}". "{}"'.format(pathway_1, reference_pathway_db, mapping_statement))
                        continue

                    if is_valid_pathway(manager_dict, compared_pathway_db, pathway_2) is False:
                        log.error(
                            '"{}" not found in "{}". "{}"'.format(pathway_2, compared_pathway_db, mapping_statement))
                        continue

                    mapping, _ = compath_manager.get_or_create_mapping(
                        reference_pathway_db,
                        manager_dict[reference_pathway_db].get_pathway_by_name(pathway_1).resource_id,
                        pathway_1,
                        compared_pathway_db,
                        manager_dict[compared_pathway_db].get_pathway_by_name(pathway_2).resource_id,
                        pathway_2,
                        IS_PART_OF,
                        curator
                    )

                    mapping, _ = compath_manager.accept_mapping(mapping.id)

                else:
                    pathway_2 = remove_star_from_pathway_name(pathway_2)

                    # Ensures the pathways exist in their corresponding managers
                    if is_valid_pathway(manager_dict, compared_pathway_db, pathway_1) is False:
                        log.error(
                            '"{}" not found in "{}". "{}"'.format(pathway_1, compared_pathway_db, mapping_statement))
                        continue
                    if is_valid_pathway(manager_dict, reference_pathway_db, pathway_2) is False:
                        log.error(
                            '"{}" not found in "{}". "{}"'.format(pathway_2, reference_pathway_db, mapping_statement))
                        continue

                    mapping, _ = compath_manager.get_or_create_mapping(
                        compared_pathway_db,
                        manager_dict[compared_pathway_db].get_pathway_by_name(pathway_1).resource_id,
                        pathway_1,
                        reference_pathway_db,
                        manager_dict[reference_pathway_db].get_pathway_by_name(pathway_2).resource_id,
                        pathway_2,
                        IS_PART_OF,
                        curator
                    )

                    mapping, _ = compath_manager.accept_mapping(mapping.id)


            else:  # EquivalentTo

                # Ensures the pathways exist in their corresponding managers
                if is_valid_pathway(manager_dict, reference_pathway_db, pathway_1) is False:
                    log.error('"{}" not found in "{}". "{}"'.format(pathway_1, reference_pathway_db, mapping_statement))
                    continue

                if is_valid_pathway(manager_dict, compared_pathway_db, pathway_2) is False:
                    log.error('"{}" not found in "{}". "{}"'.format(pathway_2, compared_pathway_db, mapping_statement))
                    continue

                mapping, _ = compath_manager.get_or_create_mapping(
                    reference_pathway_db,
                    manager_dict[reference_pathway_db].get_pathway_by_name(pathway_1).resource_id,
                    pathway_1,
                    compared_pathway_db,
                    manager_dict[compared_pathway_db].get_pathway_by_name(pathway_2).resource_id,
                    pathway_2,
                    EQUIVALENT_TO,
                    curator
                )

                mapping, _ = compath_manager.accept_mapping(mapping.id)
