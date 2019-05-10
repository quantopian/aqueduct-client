``AqueductClient``
==================

``AqueductClient`` is a simple Python wrapper around Quantopian's Aqueduct API. 
It lets you easily run and load Pipelines.

``AqueductClient`` supports Python 2.7 and Python 3.4+.


Installation
~~~~~~~~~~~~

.. code-block:: shell

   $ pip install https://github.com/quantopian/aqueduct-client


Configuration
~~~~~~~~~~~~~

To use ``AqueductClient``, you need a Quantopian API Key.  Once you have it, there
are several ways to use it:

1) Use a credentials file:  create ``~/.quantopian/credentials`` and put the following in it: 

  .. code-block:: shell

      [default]
      API_KEY = your_api_key

2) Use environment variables: set ``QUANTOPIAN_API_KEY`` to your API key.

3) Pass your API key directly into the ``AqueductClient`` constructor using the `api_key` kwarg.


Usage
-----

Note: Fuller documentation will be coming soon.

To use ``AqueductClient``, create an instance. In this case, we are loading credentials from disk or environment variable.

.. code-block:: python

  from aqueduct-client import AqueductClient

  client = AqueductClient()

To run a new pipeline, use ``create_new_pipeline``.  Required parameters are ``code`` (string), ``start_date`` and ``end_date`` (YYYY-MM-DD strings).  Optional parameters are  ``name`` (string), ``params`` (a dict of parameters to pass to your pipeline), and ``asset_identifier_format`` (which can be "symbol" (default), "sid", and "fsym_region_id").  ``create_new_pipeline`` returns an id, which you can pass to ``get_pipeline`` to monitor this pipeline's execution status.


``get_all_pipelines`` and ``get_pipeline(id)`` lets you load existing pipelines.  Each pipeline has a ``status`` field, which can be ``RUNNING``, ``SUCCESS``, or ``FAILED``.

For a successful pipeline, ``get_results_dataframe(id)`` loads that pipeline's results into a pandas DataFrame.  For a failed pipeline, ``client.get_error(id)`` shows you the information about the error.
