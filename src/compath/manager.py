# -*- coding: utf-8 -*-

""" This module the database manager of ComPath"""

import datetime
import logging

from bio2bel.utils import get_connection
from sqlalchemy import and_
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from . import managers
from .constants import MODULE_NAME
from .models import Base, PathwayMapping, User, Vote

__all__ = [
    'Manager'
]

log = logging.getLogger(__name__)


def _flip_service_order(service_1_name, service_2_name):
    """Decides whether the service order should be flipped (true if they should be)

    :param str service_1_name:
    :param str service_2_name:
    :rtype: bool
    """
    if service_1_name == service_2_name:
        return False

    return service_1_name > service_2_name


def _ensure_manager(name):
    if name not in managers:
        raise ValueError('Manager does not exist for {}'.format(name))


class Manager(object):
    """Database manager"""

    """Query methods"""

    def count_votes(self):
        """Counts the votes in the database

        :rtype: int
        """
        return self.session.query(Vote).count()

    def count_mappings(self):
        """Counts the mappings in the database

        :rtype: int
        """
        return self.session.query(PathwayMapping).count()

    def count_users(self):
        """Counts the Users in the database

        :rtype: int
        """
        return self.session.query(User).count()

    def get_mappings(self):
        """Get all mappings in the database

        :rtype: list[PathwayMapping]
        """
        return self.session.query(PathwayMapping).all()

    def get_vote_by_id(self, vote_id):
        """Gets a vote by its id

        :param str vote_id: identifier
        :rtype: Optional[Vote]
        """
        return self.session.query(Vote).filter(Vote.id == vote_id).one_or_none()

    def get_vote(self, user, mapping):
        """Gets a vote

        :param User user: User instance
        :param PathwayMapping mapping: Mapping instance
        :rtype: Optional[Vote]
        """
        return self.session.query(Vote).filter(and_(Vote.user == user, Vote.mapping == mapping)).one_or_none()

    def get_mapping(self, service_1_name, pathway_1_id, pathway_1_name, service_2_name, pathway_2_id, pathway_2_name):
        """Query mapping in the database

        :param str service_1_name: manager name of the service 1
        :param str pathway_1_name: pathway 1 name
        :param str pathway_1_id: pathway 1 id
        :param str service_2_name: manager name of the service 1
        :param str pathway_2_name: pathway 2 name
        :param str pathway_2_id: pathway 2 id
        :rtype: Optional[Mapping]
        """
        mapping_filter = and_(
            PathwayMapping.service_1_name == service_1_name,
            PathwayMapping.service_1_pathway_id == pathway_1_id,
            PathwayMapping.service_1_pathway_name == pathway_1_name,
            PathwayMapping.service_2_name == service_2_name,
            PathwayMapping.service_2_pathway_id == pathway_2_id,
            PathwayMapping.service_2_pathway_name == pathway_2_name,
        )

        return self.session.query(PathwayMapping).filter(mapping_filter).one_or_none()

    def get_mapping_by_id(self, mapping_id):
        """Gets a mapping by its id

        :param int mapping_id: mapping id
        :rtype: Optional[PathwayMapping]
        """
        return self.session.query(PathwayMapping).filter(PathwayMapping.id == mapping_id).one_or_none()

    def get_or_create_vote(self, user, mapping, vote_type=True):
        """Gets or create vote

        :param User user: User instance
        :param PathwayMapping mapping: Mapping instance
        :param Optional[Vote.type] vote_type: vote type
        :rtype: Vote
        """
        vote = self.get_vote(user, mapping)

        if vote is None:
            vote = Vote(
                user=user,
                mapping=mapping,
                type=vote_type
            )

            self.session.add(vote)
            self.session.commit()

        # If there was already a vote, and it's being changed
        elif vote_type is not None:
            vote.type = vote_type
            vote.changed = datetime.datetime.utcnow()
            self.session.commit()

        return vote

    def get_or_create_mapping(self, service_1_name, pathway_1_id, pathway_1_name, service_2_name, pathway_2_id,
                              pathway_2_name, user):
        """Gets or creates a mapping

        :param str service_1_name: manager name of the service 1
        :param str pathway_1_name: pathway 1 name
        :param str pathway_1_id: pathway 1 id
        :param str service_2_name: manager name of the service 1
        :param str pathway_2_name: pathway 2 name
        :param str pathway_2_id: pathway 2 id
        :param User user: the user
        :return: PathwayMapping and boolean indicating if the mapping was created or not
        :rtype: tuple[PathwayMapping,bool]
        """
        if _flip_service_order(service_1_name, service_2_name):
            return self.get_or_create_mapping(
                service_2_name,
                pathway_2_id,
                pathway_2_name,
                service_1_name,
                pathway_1_id,
                pathway_1_name,
                user
            )

        _ensure_manager(service_1_name)
        _ensure_manager(service_2_name)

        mapping = self.get_mapping(
            service_1_name=service_1_name,
            pathway_1_id=pathway_1_id,
            pathway_1_name=pathway_1_name,
            service_2_name=service_2_name,
            pathway_2_id=pathway_2_id,
            pathway_2_name=pathway_2_name,
        )

        if mapping is not None:
            _ = self.claim_mapping(mapping, user)

            return mapping, False

        mapping = PathwayMapping(
            service_1_name=service_1_name,
            service_1_pathway_id=pathway_1_id,
            service_1_pathway_name=pathway_1_name,
            service_2_name=service_2_name,
            service_2_pathway_id=pathway_2_id,
            service_2_pathway_name=pathway_2_name,
        )

        vote = Vote(
            mapping=mapping,
            user=user
        )

        self.session.add(mapping)
        self.session.add(vote)
        mapping.creators.append(user)
        self.session.commit()

        return mapping, True

    """Custom Model Manipulations"""

    def claim_mapping(self, mapping, user):
        """Checks if user has already established the mapping, if not claims it

        :param PathwayMapping mapping: Mapping instance
        :param User user: User
        :rtype: bool
        :return: if mapping was assigned to user
        """

        if user in mapping.creators:
            return False

        mapping.creators.append(user)
        _ = self.get_or_create_vote(user, mapping)
        return True

    def accept_mapping(self, mapping_id):
        """Accepts established mapping (from user or curator consensus)

        :param int mapping_id: mapping id
        :rtype: tuple[PathwayMapping,bool]
        :return: mapping and boolean that indicates if transaction was made
        """
        mapping = self.get_mapping_by_id(mapping_id)

        if not mapping:
            return None, False

        if mapping.accepted:
            return mapping, False

        mapping.accepted = True
        self.session.commit()
        return mapping, True

    # def get_mappings_with_pathway


class RealManager(Manager):
    def __init__(self, connection=None):
        self.connection = get_connection(MODULE_NAME, connection)
        self.engine = create_engine(self.connection)
        self.session_maker = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
        self.session = scoped_session(self.session_maker)
        self.create_all()

        # Add all available managers

    def create_all(self, check_first=True):
        """Create tables for Bio2BEL KEGG"""
        Base.metadata.create_all(self.engine, checkfirst=check_first)

    def drop_all(self, check_first=True):
        """Drop all tables for Bio2BEL KEGG"""
        Base.metadata.drop_all(self.engine, checkfirst=check_first)
