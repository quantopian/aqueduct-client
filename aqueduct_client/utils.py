import os

import pandas as pd

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
