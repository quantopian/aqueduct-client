from .aqueduct_client import create_client
from ._version import get_versions

__all__ = [
    'create_client',
]

__version__ = get_versions()['version']
del get_versions
