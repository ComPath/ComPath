# -*- coding: utf-8 -*-

"""ComPath database model"""

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

from .constants import MODULE_NAME

Base = declarative_base()

TABLE_PREFIX = MODULE_NAME
MAPPING_TABLE_NAME = '{}_mapping'.format(TABLE_PREFIX)
VOTE_TABLE_NAME = '{}_vote'.format(TABLE_PREFIX)
USER_TABLE_NAME = '{}_user'.format(TABLE_PREFIX)


class User(Base):
    """User table"""
    __tablename__ = USER_TABLE_NAME

    id = Column(Integer, primary_key=True)


class Mapping(Base):
    """Mapping Table"""
    __tablename__ = MAPPING_TABLE_NAME

    id = Column(Integer, primary_key=True)

    service_1_name = Column(String(255))
    service_1_pathway_id = Column(String(255))
    service_2_name = Column(String(255))
    service_2_pathway_id = Column(String(255))

    accepted = Column(Boolean)
    creator_id = Column(Integer, ForeignKey(User.id), nullable=False)
    creator = relationship(User, backref=backref('mappings'))


class Vote(Base):
    """Vote Table"""
    __tablename__ = VOTE_TABLE_NAME

    id = Column(Integer, primary_key=True)
    mapping_id = Column(Integer, ForeignKey(Mapping.id), nullable=False)
    mapping = relationship(Mapping, backref=backref('votes'))

    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    user = relationship(User, backref=backref('votes'))
