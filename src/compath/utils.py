# -*- coding: utf-8 -*-

from pandas import DataFrame, Series


# modified from https://stackoverflow.com/questions/19736080/creating-dataframe-from-a-dictionary-where-entries-have-different-lengths

def dict_to_pandas_df(dictionary):
    """Transforms pandas df into a dict

    :param dict dictionary:
    :rtype pandas.DataFrame:
    :return: pandas dataframe
    """
    return DataFrame(
        dict([
            (k, Series(list(v)))
            for k, v in dictionary.items()
        ])
    )
