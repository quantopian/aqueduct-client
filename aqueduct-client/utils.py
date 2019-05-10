import os
import logging

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


def load_api_key():
    # check in credentials file
    path = os.path.expanduser("~/.quantopian/credentials")

    if os.path.isfile(path):
    	# read the file
    	try:
    		parser = configparser.ConfigParser()
    		parser.read(path)

    		api_key = parser.get("default", "api_key")
    		if api_key is not None:
    			return api_key
    	except Exception as e:
    		logging.error(
    			"Error parsing credentials file at {creds_path}, exception={exc}".format(
    				creds_path=path,
    				e=exc
    			)
    		)

    # then check in env var
    api_key = os.getenv("QUANTOPIAN_API_KEY", None)

    return api_key
