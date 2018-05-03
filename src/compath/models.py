# -*- coding: utf-8 -*-

"""ComPath database model."""

import datetime

from compath.constants import MODULE_NAME, VOTE_ACCEPTANCE

from flask_security import RoleMixin, UserMixin

from sqlalchemy import and_, or_, Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship

Base = declarative_base()

TABLE_PREFIX = MODULE_NAME
MAPPING_TABLE_NAME = '{}_mapping'.format(TABLE_PREFIX)
VOTE_TABLE_NAME = '{}_vote'.format(TABLE_PREFIX)
USER_TABLE_NAME = '{}_user'.format(TABLE_PREFIX)
ROLE_TABLE_NAME = '{}_role'.format(TABLE_PREFIX)
ROLES_USERS_TABLE_NAME = '{}_roles_users'.format(TABLE_PREFIX)
MAPPING_USER_TABLE_NAME = '{}_mappings_users'.format(TABLE_PREFIX)

roles_users = Table(
    ROLES_USERS_TABLE_NAME,
    Base.metadata,
    Column('user_id', Integer(), ForeignKey('{}.id'.format(USER_TABLE_NAME))),
    Column('role_id', Integer(), ForeignKey('{}.id'.format(ROLE_TABLE_NAME)))
)

mappings_users = Table(
    MAPPING_USER_TABLE_NAME,
    Base.metadata,
    Column('mapping_id', Integer(), ForeignKey('{}.id'.format(MAPPING_TABLE_NAME))),
    Column('user_id', Integer(), ForeignKey('{}.id'.format(USER_TABLE_NAME)))
)


class User(Base, UserMixin):
    """User table."""

    __tablename__ = USER_TABLE_NAME
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    password = Column(String(255))
    active = Column(Boolean())
    confirmed_at = Column(DateTime())
    roles = relationship('Role', secondary=roles_users, backref=backref('users', lazy='dynamic'))

    @property
    def is_admin(self):
        """Is this user an administrator?."""
        return self.has_role('admin')

    def __str__(self):
        """Return email."""
        return self.email


class Role(Base, RoleMixin):
    """Role table."""
    __tablename__ = ROLE_TABLE_NAME
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    description = Column(String(255))

    def __str__(self):
        """Return name of the role."""
        return self.name


class PathwayMapping(Base):
    """Mapping table."""

    __tablename__ = MAPPING_TABLE_NAME

    id = Column(Integer, primary_key=True)

    service_1_name = Column(String(255), doc='service name (e.g., KEGG or Reactome')
    service_1_pathway_id = Column(String(255), doc='pathway 1 id')
    service_1_pathway_name = Column(String(255), doc='pathway 1 name')

    service_2_name = Column(String(255), doc='service name (e.g., KEGG or Reactome')
    service_2_pathway_id = Column(String(255), doc='pathway 2 id')
    service_2_pathway_name = Column(String(255), doc='pathway 2 name')

    type = Column(String(255), doc='Type of Mapping (isPartOf or equivalentTo)')

    accepted = Column(Boolean, doc='accepted mapping by the admin/curator consensus')
    creators = relationship('User', secondary=mappings_users, backref='mappings')

    def __str__(self):
        """Return mapping info"""
        return '{} mapping from {}:{} to {}:{}'.format(
            self.type,
            self.service_1_name,
            self.service_1_pathway_name,
            self.service_2_name,
            self.service_2_pathway_name
        )

    def get_complement_mapping_info(self, service_name, pathway_id, pathway_name):
        """Return the info corresponding to the other pathway in a mapping.

        :param PathwayMapping mapping:
        :param str service_name: reference service name
        :param str pathway_id: reference pathway id
        :param str pathway_name: reference pathway name
        :rtype: tuple[str,str,str]
        """

        if self.service_1_name == service_name and \
                self.service_1_pathway_id == pathway_id and \
                self.service_1_pathway_name == pathway_name:
            return self.service_2_name, self.service_2_pathway_id, self.service_2_pathway_name

        else:
            return self.service_1_name, self.service_1_pathway_id, self.service_1_pathway_name

    @staticmethod
    def has_pathway_tuple(type, service_name, pathway_id, pathway_name):
        """Return a filter to get all mappings matching type, service and pathway name and id."""
        return or_(
            and_(
                PathwayMapping.service_1_name == service_name,
                PathwayMapping.service_1_pathway_id == pathway_id,
                PathwayMapping.service_1_pathway_name == pathway_name,
                PathwayMapping.type == type
            ),
            and_(
                PathwayMapping.service_2_name == service_name,
                PathwayMapping.service_2_pathway_id == pathway_id,
                PathwayMapping.service_2_pathway_name == pathway_name,
                PathwayMapping.type == type
            )
        )

    @staticmethod
    def has_pathway(service_name, pathway_id, pathway_name):
        """Return a filter to get all mappings matching service and pathway name and id."""
        return or_(
            and_(
                PathwayMapping.service_1_name == service_name,
                PathwayMapping.service_1_pathway_id == pathway_id,
                PathwayMapping.service_1_pathway_name == pathway_name,
            ),
            and_(
                PathwayMapping.service_2_name == service_name,
                PathwayMapping.service_2_pathway_id == pathway_id,
                PathwayMapping.service_2_pathway_name == pathway_name,
            )
        )

    @staticmethod
    def has_database_pathway(service_name):
        """Return a filter to get all mappings matching service a name."""
        return or_(
            PathwayMapping.service_1_name == service_name,
            PathwayMapping.service_2_name == service_name,
        )

    @property
    def count_votes(self):
        """Return the number of votes for this mapping.

        :rtype: int
        """
        return len(self.votes)

    @property
    def count_creators(self):
        """Return the number of creator that claimed this mapping.

        :rtype: int
        """
        return len(self.creators)

    @property
    def count_up_votes(self):
        """Return the number of up votes for this mapping.

        :rtype: int
        """
        return self.votes.filter(Vote.type == True).count()

    @property
    def count_down_votes(self):
        """Return the number of down votes for this mapping.

        :rtype: int
        """
        return self.votes.filter(Vote.type == False).count()

    @property
    def is_acceptable(self):
        """Return true if the mapping has enough votes to be accepted.

        :rtype: bool
        """
        return self.votes.filter(Vote.type == True).count() >= VOTE_ACCEPTANCE

    def get_user_vote(self, user):
        """Return votes given by the user."""
        return self.votes.filter(Vote.user == user).one_or_none()


class Vote(Base):
    """Vote table."""

    __tablename__ = VOTE_TABLE_NAME

    id = Column(Integer, primary_key=True)
    mapping_id = Column(Integer, ForeignKey(PathwayMapping.id), nullable=False)
    mapping = relationship(PathwayMapping, backref=backref('votes', lazy='dynamic', cascade='all, delete-orphan'))
    changed = Column(DateTime, default=datetime.datetime.utcnow)

    type = Column(Boolean, default=True, nullable=False, doc='Type of vote, by default is up-vote')

    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    user = relationship(User, backref=backref('votes'))
