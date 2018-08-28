# -*- coding: utf-8 -*-

"""This module contains all the curation processing methods to integrate curated mappings to ComPath."""

import logging

import pandas as pd
from tqdm import tqdm

from compath import managers
from compath.constants import *
from compath.curation.utils import *
from compath.manager import Manager

log = logging.getLogger(__name__)


def get_users_from_emails(compath_manager, curator_emails):
    """Return a list with curator users.

    :param Manager compath_manager:
    :param list[str] curator_emails:
    :rtype: list[User]
    """
    curators = []
    if not curator_emails:
        default_curator = compath_manager.get_user_by_email(ADMIN_EMAIL)

        if not default_curator:
            raise EnvironmentError(
                'There is no user with the email "{}". Please create it with the "make_user" command using '
                'the command line interface of Compath'.format(ADMIN_EMAIL)
            )
        curators.append(default_curator)

    else:
        for email in curator_emails:
            curator = compath_manager.get_user_by_email(email)
            if not curator:
                raise EnvironmentError(
                    'There is no user with the email "{}". Please create it with the "make_user" command using '
                    'the command line interface of Compath'.format(email)
                )
            curators.append(curator)

    return curators


def parse_special_mappings(path, curator_emails=None, connection=None):
    """Parse special mapping file.

    :param str path: path of the excel sheet
    :param Optional[list] curator_emails: emails of the curators. Needs to be already in the database
    """
    df = pd.read_excel(path, header=1)

    if not connection:
        connection = DEFAULT_CACHE_CONNECTION

    # Loads the installed managers
    manager_dict = {
        name: ExternalManager(connection=connection)
        for name, ExternalManager in managers.items()
    }

    compath_manager = Manager.from_connection(connection=connection)

    curators = get_users_from_emails(compath_manager, curator_emails=curator_emails)

    for index, row in tqdm(df.iterrows(), total=len(df.index), desc='Loading special mappings'):

        resource_1 = row['Resource 1'].lower()
        resource_2 = row['Resource 2'].lower()
        pathway_1_id = row['Pathway identifier 1']
        pathway_2_id = row['Pathway identifier 2']

        valid_pathway_1 = is_valid_pathway_by_id(manager_dict, resource_1, pathway_1_id)
        valid_pathway_2 = is_valid_pathway_by_id(manager_dict, resource_2, pathway_2_id)

        if valid_pathway_1 is False:
            raise ValueError("Invalid Pathway Identifier: {} in {}".format(pathway_1_id, resource_1))

        if valid_pathway_2 is False:
            raise ValueError("Invalid Pathway Identifier: {} in {}".format(pathway_2_id, resource_2))

        pathway_1 = manager_dict[resource_1].get_pathway_by_id(pathway_1_id)
        pathway_2 = manager_dict[resource_2].get_pathway_by_id(pathway_2_id)

        for curator in curators:
            mapping, _ = compath_manager.get_or_create_mapping(
                resource_1,
                pathway_1.resource_id,
                pathway_1.name,
                resource_2,
                pathway_2.resource_id,
                pathway_2.name,
                row['Mapping type'],
                curator
            )

            mapping, _ = compath_manager.accept_mapping(mapping.id)


def parse_curation_template(path, reference_pathway_db, compared_pathway_db, curator_emails=None, connection=None):
    """Load the curation template excel sheet into a pandas Dataframe.

    :param str path: path of the excel sheet
    :param str reference_pathway_db: name of the manager of the reference pathway_db
    :param str compared_pathway_db: name of the manager of the compared pathway_db
    :param Optional[list] curator_emails: email of the curators. Needs to be already in the database
    :param str connection: database connection
    """
    df = pd.read_csv(path)

    if not connection:
        connection = DEFAULT_CACHE_CONNECTION

    # Loads the installed managers
    manager_dict = {
        name: ExternalManager(connection=connection)
        for name, ExternalManager in managers.items()
    }

    compath_manager = Manager.from_connection(connection=connection)

    curators = get_users_from_emails(compath_manager, curator_emails=curator_emails)

    for index, row in tqdm(df.iterrows(), total=len(df.index),
                           desc='Loading mappings for {}-{}'.format(reference_pathway_db, compared_pathway_db)):

        if row['Mapping Type'] not in MAPPING_TYPES:
            raise ValueError('Unknown type {}'.format(row['Mapping Type']))

        valid_pathway_1 = is_valid_pathway_by_id(manager_dict, row['Source Resource'], row['Source ID'])
        valid_pathway_2 = is_valid_pathway_by_id(manager_dict, row['Target Resource'], row['Target ID'])

        if valid_pathway_1 is False:
            raise ValueError("Not Valid Pathway Name: {} in {}".format(row['Source Name'], row['Source Resource']))

        if valid_pathway_2 is False:
            raise ValueError("Not Valid Pathway Name: {} in {}".format(row['Target Name'], row['Target Resource']))

        for curator in curators:
            mapping, _ = compath_manager.get_or_create_mapping(
                row['Source Resource'],
                row['Source ID'],
                manager_dict[row['Source Resource']].get_pathway_by_id(row['Source ID']).name,
                row['Target Resource'],
                row['Target ID'],
                manager_dict[row['Target Resource']].get_pathway_by_id(row['Target ID']).name,
                row['Mapping Type'],
                curator
            )

            mapping, _ = compath_manager.accept_mapping(mapping.id)
