# -*- coding: utf-8 -*-

"""This module loads the hierarchical pathway databases into ComPath."""

import logging

from compath import managers
from compath.constants import ADMIN_EMAIL, IS_PART_OF
from compath.manager import RealManager

from tqdm import tqdm

log = logging.getLogger(__name__)


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
    :param compath.manager.RealManager compath_manager: ComPath Manager
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
                pathway_1_id=children.resource_id,
                pathway_1_name=children.name,
                service_2_name=pathway_database,
                pathway_2_id=pathway.resource_id,
                pathway_2_name=pathway.name,
                mapping_type=IS_PART_OF,
                user=curator
            )

            if created:
                mappings_created += 1
    return mappings_created


def load_hierarchy(curator_email=None):
    """Load the hierarchical relationships for the managers containing them.

    :param Optional[str] curator_email: email of the admin
    """
    compath_manager = RealManager()

    curator = compath_manager.get_user_by_email(email=curator_email if curator_email else ADMIN_EMAIL)

    if not curator:
        raise EnvironmentError(
            'There is no user with the email "{}". Please create it with the "make_user" command using '
            'the command line interface of Compath'
        )

    for pathway_database, ExternalManager in managers.items():

        pathway_db_manager = ExternalManager()

        if not hasattr(pathway_db_manager, 'has_hierarchy'):
            continue

        log.info("Loading hierarchies for {}".format(pathway_database))

        pathways = pathway_db_manager.get_all_pathways()

        if pathway_database == 'reactome':
            pathways = _reactome_wrapper(pathways)

        log.info("Searching for hierarchical relationships in {} pathways".format(len(pathways)))

        mapping_created = create_hierarchical_mappings(pathways, compath_manager, pathway_database, curator)

        log.info("{} hierarchical mappings created in {}".format(mapping_created, pathway_database))
