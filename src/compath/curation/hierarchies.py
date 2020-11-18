# -*- coding: utf-8 -*-

"""This module loads the hierarchical pathway databases into ComPath."""

import logging
from typing import Optional

from tqdm import tqdm

from bio2bel.compath import iter_compath_managers
from ..constants import ADMIN_EMAIL, IS_PART_OF
from ..manager import Manager

logger = logging.getLogger(__name__)


def _reactome_wrapper(pathways):
    """Filter down the human pathways.

    :param list[Pathway] pathways: list of pathways
    :rtype: list[Pathway]
    :return: human pathways
    """
    return [
        pathway
        for pathway in pathways
        if pathway.species.name == 'Homo sapiens'
    ]


def create_hierarchical_mappings(pathways, compath_manager, pathway_database, curator):
    """Iterate over pathway objects and creates hierarchies if exist.

    :param list[Pathway] pathways: list of pathways
    :param compath.manager.Manager compath_manager: ComPath Manager
    :param str pathway_database: Name of the pathway database
    :param compath.models.User curator: Curator user
    :return: number of created mappings
    :rtype: int
    """
    mappings_created = 0

    for pathway in tqdm(pathways, desc='Loading hierarchies'):
        if not pathway.children:
            continue

        for children in pathway.children:
            mapping, created = compath_manager.get_or_create_mapping(
                service_1_name=pathway_database,
                pathway_1_id=children.identifier,
                pathway_1_name=children.name,
                service_2_name=pathway_database,
                pathway_2_id=pathway.identifier,
                pathway_2_name=pathway.name,
                mapping_type=IS_PART_OF,
                user=curator
            )

            if created:
                mappings_created += 1

    return mappings_created


def load_hierarchy(*, connection: Optional[str] = None, curator_email: Optional[str] = None):
    """Load the hierarchical relationships for the managers containing them.

    :param connection:
    :param curator_email: email of the admin
    """
    compath_manager = Manager.from_connection(connection)

    curator = compath_manager.get_user_by_email(email=curator_email if curator_email else ADMIN_EMAIL)

    if not curator:
        raise EnvironmentError(
            'There is no user with the email "{}". Please create it with the "make_user" command using '
            'the command line interface of Compath'
        )

    for pathway_database, pathway_manager in iter_compath_managers(connection=connection):
        if not hasattr(pathway_manager, 'has_hierarchy'):
            continue

        logger.info("Loading hierarchies for %s", pathway_database)

        pathways = pathway_manager.list_pathways()

        if pathway_database == 'reactome':
            pathways = _reactome_wrapper(pathways)

        logger.info(
            "Searching for hierarchical relationships in %s %s pathways",
            len(pathways), pathway_database,
        )

        counter_mappings_created = create_hierarchical_mappings(pathways, compath_manager, pathway_database, curator)

        logger.info("{} hierarchical mappings created in {}".format(counter_mappings_created, pathway_database))
