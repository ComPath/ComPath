# -*- coding: utf-8 -*-

"""This module contains all the curation processing methods to integrate curated mappings to ComPath."""

import logging
from tqdm import tqdm

import pandas as pd

from compath import managers
from compath.constants import *
from compath.curation.utils import *
from compath.manager import RealManager

log = logging.getLogger(__name__)


def parse_curation_template(path, reference_pathway_db, compared_pathway_db, admin_email=None):
    """Load the curation template excel sheet into a pandas Dataframe.

    :param str path: path of the excel sheet
    :param str reference_pathway_db: name of the manager of the reference pathway_db
    :param str compared_pathway_db: name of the manager of the compared pathway_db
    :param str admin_email: email of the admin. Needs to be already in the database
    """
    df = pd.read_excel(path, index_col=0)

    # Loads the installed managers
    manager_dict = {
        name: ExternalManager(connection=DEFAULT_CACHE_CONNECTION)
        for name, ExternalManager in managers.items()
    }

    compath_manager = RealManager()

    curator = compath_manager.get_user_by_email(email=admin_email if admin_email else ADMIN_EMAIL)

    if not curator:
        raise EnvironmentError(
            'There is no user with the email "{}". Please create it with the "make_user" command using '
            'the command line interface of Compath'
        )

    for index, row in tqdm(df.iterrows(), desc='Loading mappings for {}-{}'.format(reference_pathway_db, compared_pathway_db)):

        # Add equivalent mappings
        equivalent_to_mappings = row['equivalentTo Mappings']

        if not pd.isnull(equivalent_to_mappings):  # if equivalent pathway is found

            for mapping_statement in equivalent_to_mappings.split("\n"):

                if mapping_statement == '':
                    continue

                pathway_1, pathway_2 = get_pathways_from_statement(mapping_statement, "equivalentTo")

                valid_pathway_1 = is_valid_pathway(manager_dict, reference_pathway_db, pathway_1)
                valid_pathway_2 = is_valid_pathway(manager_dict, compared_pathway_db, pathway_2)

                if valid_pathway_1 is False:
                    raise ValueError("Not Valid Pathway Name: {} in {}".format(pathway_1, reference_pathway_db))

                if valid_pathway_2 is False:
                    raise ValueError("Not Valid Pathway Name: {} in {}".format(pathway_2, compared_pathway_db))

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

        # Add hierarchical mappings
        is_part_of_mappings = row['isPartOf Mappings']

        if not pd.isnull(is_part_of_mappings):

            for mapping_statement in is_part_of_mappings.split('\n'):

                if mapping_statement == '':
                    continue

                pathway_1, pathway_2 = get_pathways_from_statement(mapping_statement, 'isPartOf')

                if "*" in pathway_1:
                    pathway_1 = remove_star_from_pathway_name(pathway_1)

                    valid_pathway_1 = is_valid_pathway(manager_dict, reference_pathway_db, pathway_1)
                    valid_pathway_2 = is_valid_pathway(manager_dict, compared_pathway_db, pathway_2)

                    if valid_pathway_1 is False:
                        raise ValueError("Not Valid Pathway Name: {} in {}".format(pathway_1, reference_pathway_db))

                    if valid_pathway_2 is False:
                        raise ValueError("Not Valid Pathway Name: {} in {}".format(pathway_2, compared_pathway_db))

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

                    valid_pathway_1 = is_valid_pathway(manager_dict, compared_pathway_db, pathway_1)
                    valid_pathway_2 = is_valid_pathway(manager_dict, reference_pathway_db, pathway_2)

                    if valid_pathway_1 is False:
                        raise ValueError("Not Valid Pathway Name: {} in {}".format(pathway_1, compared_pathway_db))

                    if valid_pathway_2 is False:
                        raise ValueError("Not Valid Pathway Name: {} in {}".format(pathway_2, reference_pathway_db))

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
