# -*- coding: utf-8 -*-

"""Utilities for web services."""

from typing import Optional

from bio2bel.compath import CompathPathwayMixin
from ..state import bio2bel_managers

__all__ = [
    'get_pathway_model_by_id',
]


def get_pathway_model_by_id(prefix: str, identifier: str) -> Optional[CompathPathwayMixin]:
    """Return the pathway object from the resource manager.

    :param prefix: name of the manager
    :param identifier: pathway id
    :return: pathway if exists
    """
    return bio2bel_managers[prefix.lower()].get_pathway_by_id(identifier)
