``AqueductClient``
==================

``AqueductClient`` is a simple Python wrapper around Quantopian's Aqueduct API.
It lets you easily create Pipeline executions and load their results.

``AqueductClient`` supports Python 2.7 and Python 3.4+.


Installation
~~~~~~~~~~~~

.. code-block:: shell

   $ pip install git+https://git@github.com/quantopian/aqueduct-client.git


Configuration
~~~~~~~~~~~~~

To use ``AqueductClient``, you need a Quantopian API Key.  Once you have it, there
are several ways to use it:

1) Use a credentials file:  create ``~/.quantopian/credentials`` (Linux or OS X) or ``%UserProfile%\.quantopian\credentials`` (Windows) and put the following in it:

  .. code-block:: shell

      [default]
      API_KEY = your_api_key

2) Use an environment variable: set ``QUANTOPIAN_API_KEY`` to your API key.

3) Pass your API key directly into the ``create_client`` method (see below) using the ``api_key`` kwarg.


Usage
~~~~~

Note: Fuller documentation will be coming soon.

To use ``AqueductClient``, create an instance. In this case, we are loading credentials from disk or environment variable.

.. code-block:: python

  from aqueduct_client import create_client

  client = create_client()

To run a new pipeline execution, use ``submit_pipeline_execution``.  Required parameters are ``code`` (string), ``start_date`` and ``end_date`` (date-like strings, dates, or Pandas timestamps).  Optional parameters are  ``name`` (string), ``params`` (a dict of parameters to pass to your pipeline), and ``asset_identifier_format`` (which can be "symbol" (default), "sid", and "fsym_region_id").  ``submit_pipeline_execution`` returns an id, which you can pass to ``get_pipeline_execution`` to monitor this pipeline's execution status.


``get_all_pipeline_executions`` and ``get_pipeline_execution(id)`` let you load existing pipelines.  Each pipeline has a ``status`` field, which can be ``IN-PROGRESS``, ``SUCCESS``, or ``FAILED``.

For a successful pipeline, ``get_pipeline_results_dataframe(id)`` loads that pipeline's results into a pandas DataFrame.  For a failed pipeline, ``get_pipeline_execution_error(id)`` shows you the information about the error.
