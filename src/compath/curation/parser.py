# -*- coding: utf-8 -*-

"""This module contains all the curation processing methods to integrate curated mappings to ComPath."""

import logging
from typing import List, Mapping, Optional

import pandas as pd
from tqdm import tqdm

from bio2bel.compath import CompathManager, get_compath_managers
from ..constants import ADMIN_EMAIL, MAPPING_TYPES
from ..manager import Manager
from ..models import User

logger = logging.getLogger(__name__)


def get_users_from_emails(compath_manager: Manager, curator_emails: Optional[List[str]]) -> List[User]:
    """Return a list with curator users."""
    curators = []
    if not curator_emails:
        default_curator = compath_manager.get_user_by_email(ADMIN_EMAIL)

        if not default_curator:
            raise EnvironmentError(
                'There is no user with the email "{}". Please create it with the "make_user" command using '
                'the command line interface of ComPath'.format(ADMIN_EMAIL)
            )
        curators.append(default_curator)

    else:
        for email in curator_emails:
            curator = compath_manager.get_user_by_email(email)
            if not curator:
                curator = User(email=email, password='alpine')
                compath_manager.session.add(curator)
                compath_manager.session.commit()
                logger.warning('created user %s. Please change password.', curator)
            curators.append(curator)

    return curators


def parse_special_mappings(
    path: str,
    curator_emails: Optional[List[str]] = None,
    connection: Optional[str] = None,
    compath_manager: Optional[Manager] = None,
    bio2bel_managers: Optional[Mapping[str, CompathManager]] = None,
):
    """Parse special mapping file.

    :param path: path of the excel sheet
    :param curator_emails: emails of the curators. Needs to be already in the database
    """
    logger.info('loading special mappings from %s', path)
    df = pd.read_csv(path)

    if bio2bel_managers is None:
        # Loads the installed managers
        bio2bel_managers: Mapping[str, CompathManager] = get_compath_managers(connection=connection)
    if compath_manager is None:
        compath_manager = Manager.from_connection(connection=connection)

    curators = get_users_from_emails(compath_manager, curator_emails=curator_emails)
    logger.info('got %d curators', len(curators))

    it = tqdm(df.values, total=len(df.index), desc='Loading special mappings')
    for r1, p1_identifier, p1_name, m_type, r2, p2_identifier, p2_name, _explanation, _curator in it:
        pathway_1 = bio2bel_managers[r1].get_pathway_by_id(p1_identifier)
        pathway_2 = bio2bel_managers[r2].get_pathway_by_id(p2_identifier)

        skip = False
        if pathway_1 is None:
            logger.warning('invalid source pathway: %s:%s ! %s', r1, p1_identifier, p1_name)
            skip = True
        if pathway_2 is None:
            logger.warning('invalid source pathway: %s:%s ! %s', r2, p2_identifier, p2_name)
            skip = True
        if skip:
            continue

        for curator in curators:
            mapping, _ = compath_manager.get_or_create_mapping(
                r1,
                pathway_1.identifier,
                pathway_1.name,
                r2,
                pathway_2.identifier,
                pathway_2.name,
                m_type,
                curator,
            )

            mapping, _ = compath_manager.accept_mapping(mapping.id)


def parse_curation_template(
    path: str,
    reference_pathway_db: str,
    compared_pathway_db: str,
    curator_emails: Optional[List[str]] = None,
    connection: Optional[str] = None,
    compath_manager: Optional[Manager] = None,
    bio2bel_managers: Optional[Mapping[str, CompathManager]] = None,
):
    """Load the curation template excel sheet into a pandas Dataframe.

    :param path: path of the excel sheet
    :param reference_pathway_db: name of the manager of the reference pathway_db
    :param compared_pathway_db: name of the manager of the compared pathway_db
    :param curator_emails: email of the curators. Needs to be already in the database
    :param connection: database connection
    """
    logger.info('loading mapping from %s', path)
    df = pd.read_csv(path)

    if bio2bel_managers is None:
        # Loads the installed managers
        bio2bel_managers: Mapping[str, CompathManager] = get_compath_managers(connection=connection)

    if compath_manager is None:
        compath_manager = Manager.from_connection(connection=connection)

    curators = get_users_from_emails(compath_manager, curator_emails=curator_emails)

    it = tqdm(
        df.iterrows(),
        total=len(df.index),
        desc=f'Loading mappings for {reference_pathway_db}-{compared_pathway_db}',
    )
    for _, row in it:
        if row['Mapping Type'] not in MAPPING_TYPES:
            raise ValueError('Unknown type {}'.format(row['Mapping Type']))

        pathway_1 = bio2bel_managers[row['Source Resource']].get_pathway_by_id(row['Source ID'])
        pathway_2 = bio2bel_managers[row['Target Resource']].get_pathway_by_id(row['Target ID'])

        skip = False
        if pathway_1 is None:
            it.write("Not Valid Pathway Name: {} in {}".format(row['Source Name'], row['Source Resource']))
            skip = True
        if pathway_2 is None:
            it.write("Not Valid Pathway Name: {} in {}".format(row['Target Name'], row['Target Resource']))
            skip = True
        if skip:
            continue

        for curator in curators:
            mapping, _ = compath_manager.get_or_create_mapping(
                row['Source Resource'],
                row['Source ID'],
                pathway_1.name,
                row['Target Resource'],
                row['Target ID'],
                pathway_2.name,
                row['Mapping Type'],
                curator,
            )
            mapping, _ = compath_manager.accept_mapping(mapping.id)
