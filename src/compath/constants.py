# -*- coding: utf-8 -*-

"""This module contains all the constants used in ComPath repo"""

from bio2bel.utils import get_connection, get_data_dir

MODULE_NAME = 'compath'
DATA_DIR = get_data_dir(MODULE_NAME)
DEFAULT_CACHE_CONNECTION = get_connection(MODULE_NAME)
