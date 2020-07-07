import os

import pandas as pd
import numpy as np

try:
    # py3
    from configparser import ConfigParser
except ImportError:
    # py2
    from ConfigParser import SafeConfigParser as ConfigParser


def load_api_key():
    """
    Utility method that attempts to load the Quantopian API key.
    It first checks the filesystem at ~/.quantopian/credentials
    (or the Windows equivalent), and then tries to load from
    an environment variable.

    Raises
    ------
    If an api key cannot be found in either location, we raise
    ValueError.

    Returns
    -------
    str
        The api key that we found.
    """
    path = os.path.expanduser("~/.quantopian/credentials")

    if os.path.isfile(path):
        # read the file
        try:
            parser = ConfigParser()
            parser.read(path)

            api_key = parser.get("default", "API_KEY")
            if api_key is not None:
                return api_key
        except Exception as e:
            raise ValueError(
                "Error parsing credentials file at {creds_path}, "
                "exception={exc}".format(
                    creds_path=path,
                    exc=e,
                )
            )

    api_key = os.getenv("QUANTOPIAN_API_KEY", None)

    if api_key is None:
        raise ValueError("No API key found!")

    return api_key


def normalize_date_input(date_like):
    """
    Utility method that tries to parse a date-like object and
    returns a datetime.date.
    """
    try:
        timestamp = pd.Timestamp(date_like)
    except ValueError:
        raise ValueError("Could not parse date: {date}".format(date=date_like))

    if timestamp.normalize() != timestamp:
        raise ValueError("Date {date} is not a date".format(date=date_like))

    return timestamp.date()


def construct_returns_data_code(factor_data, periods, domain_str):
    pipeline_code = """
from quantopian.pipeline import Pipeline
from quantopian.pipeline.filters import StaticSids
from quantopian.pipeline.factors import Returns
from quantopian.pipeline.domain import {domain_str}

import numpy as np

def make_pipeline():
    return Pipeline(
        columns={column_str},
        domain={domain_str},
        screen=StaticSids({assets_str}),
    )
""".format(
        column_str=_generate_column_str(periods),
        domain_str=domain_str,
        assets_str=_generate_assets_str(factor_data),
    )

    return pipeline_code


def _generate_column_str(periods):
    period_strings = [
"'{period_name}': Returns(window_length={period_plus_one})".format(
            period_name=generate_period_name(period),
            period_plus_one=period+1
        ) for period in periods
    ]

    return "{" + ", ".join(period_strings) + ",}"


def _generate_assets_str(factor_data):
    asset_ints = list(map(int, np.array(factor_data.index.levels[1])))
    return str(asset_ints)


def generate_period_name(period_int):
    return "{}D".format(period_int)


def backshift_returns_series(series, observation_count):
    """
    Shifts a multi-indexed series backwards by N observations in
    the first level.

    Parameters
    ----------
    series: pd.Series
        A multi-indexed series, where the first index level is a
        DatetimeIndex.

    observation_count: int
        The number of observations by which to backshift the series.

    Returns
    -------
    pd.Series
        The backshifted series.
    """
    ix = series.index
    dates, sids = ix.levels
    date_labels, sid_labels = map(np.array, ix.labels)

    # Output date labels will contain the all but the last `observation_count`
    # dates.
    new_dates = dates[:-observation_count]

    # Output data will remove the first M rows, where M is the index of the
    # last record with one of the first `observation_count` dates.
    cutoff = date_labels.searchsorted(observation_count)
    new_date_labels = date_labels[cutoff:] - observation_count
    new_sid_labels = sid_labels[cutoff:]
    new_values = series.values[cutoff:]

    assert new_date_labels[0] == 0

    new_index = pd.MultiIndex(
        levels=[new_dates, sids],
        labels=[new_date_labels, new_sid_labels],
        sortorder=1,
        names=ix.names,
    )

    new_series = pd.Series(data=new_values, index=new_index)
    new_series.sort_index(level=series.index.names, inplace=True)

    return new_series
