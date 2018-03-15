# -*- coding: utf-8 -*-

"""ComPath database model"""

from flask_security import RoleMixin, UserMixin
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship

from .constants import MODULE_NAME

Base = declarative_base()

TABLE_PREFIX = MODULE_NAME
MAPPING_TABLE_NAME = '{}_mapping'.format(TABLE_PREFIX)
VOTE_TABLE_NAME = '{}_vote'.format(TABLE_PREFIX)
USER_TABLE_NAME = '{}_user'.format(TABLE_PREFIX)
ROLE_TABLE_NAME = '{}_role'.format(TABLE_PREFIX)

roles_users = Table(
    'roles_users',
    Base.metadata,
    Column('user_id', Integer(), ForeignKey('{}.id'.format(USER_TABLE_NAME))),
    Column('role_id', Integer(), ForeignKey('{}.id'.format(ROLE_TABLE_NAME)))
)


class User(Base, UserMixin):
    """User table"""
    __tablename__ = ROLE_TABLE_NAME
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    password = Column(String(255))
    active = Column(Boolean())
    confirmed_at = Column(DateTime())
    roles = relationship('Role', secondary=roles_users, backref=backref('users', lazy='dynamic'))

    @property
    def is_admin(self):
        """Is this user an administrator?"""
        return self.has_role('admin')

    def __str__(self):
        return self.email


class Role(Base, RoleMixin):
    __tablename__ = USER_TABLE_NAME
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    description = Column(String(255))


class PathwayMapping(Base):
    """Mapping Table"""
    __tablename__ = MAPPING_TABLE_NAME

    id = Column(Integer, primary_key=True)

    service_1_name = Column(String(255), doc='service name (e.g., KEGG or Reactome')
    service_1_pathway_id = Column(String(255), doc='pathway 1 id')
    service_1_pathway_name = Column(String(255), doc='pathway 1 name')

    service_2_name = Column(String(255), doc='service name (e.g., KEGG or Reactome')
    service_2_pathway_id = Column(String(255), doc='pathway 2 id')
    service_2_pathway_name = Column(String(255), doc='pathway 2 name')

    accepted = Column(Boolean, doc='canonical mapping')
    creator_id = Column(Integer, ForeignKey(User.id), nullable=False)
    creator = relationship(User, backref=backref('mappings'))

    def __str__(self):
        return 'Mapping from {}:{} to {}:{}'.format(self.service_1_name, self.service_1_pathway_name,
                                                  self.service_2_name, self.service_2_pathway_name)


class Vote(Base):
    """Vote Table"""
    __tablename__ = VOTE_TABLE_NAME

    id = Column(Integer, primary_key=True)
    mapping_id = Column(Integer, ForeignKey(PathwayMapping.id), nullable=False)
    mapping = relationship(PathwayMapping, backref=backref('votes'))

    type = Column(Boolean, default=True, nullable=False, doc='Type of vote, by default is up-vote')

    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    user = relationship(User, backref=backref('votes'))
