from __future__ import annotations

import typing
from dataclasses import dataclass
from typing import Any, List, Mapping, Tuple

from flask import current_app
from flask_security.datastore import UserDatastore
from werkzeug.local import LocalProxy

from bio2bel.compath import CompathManager
from .manager import Manager

__all__ = [
    'CompathState',
    'compath_state',
    'web_manager',
    'bio2bel_managers',
]


@dataclass
class CompathState:
    """Hold state for the compath web application."""

    #: ComPath Web manager
    compath_manager: Manager
    #: User Datastore
    user_datastore: UserDatastore
    #: External managers
    bio2bel_managers: Mapping[str, CompathManager]
    #: The dates at which each manager was populated
    database_date: Mapping[str, str]

    resource_to_pathway_distribution: Mapping[str, typing.Counter[str]]

    resource_to_gene_distribution: Mapping[str, typing.Counter[str]]

    simulation_results: Mapping[str, List[float]]

    overlap: List[Mapping[str, Any]]

    resource_overview: Mapping[str, Tuple[int, int]]


compath_state: CompathState = LocalProxy(lambda: current_app.extensions['compath'])

web_manager: Manager = LocalProxy(lambda: compath_state.compath_manager)
bio2bel_managers: Mapping[str, CompathManager] = LocalProxy(lambda: compath_state.bio2bel_managers)
