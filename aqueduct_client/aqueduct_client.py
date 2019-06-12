try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

import json

import pandas as pd
import requests

from .utils import (
    load_api_key,
    normalize_date_input,
)

from .errors import ConcurrentExecutionsExceeded


def create_client(
    api_key=None,
    base_url="https://factset.quantopian.com/api/experimental/pipelines"
):
    """
    Create an AqueductClient.

    Parameters
    ----------
    api_key : str, optional
        The Quantopian API key to use.  If not given, we attempt
        to load the key from a credentials file (at ~/.quantopian/credentials
        or %UserProfile%\\.quantopian\\credentials) or from an
        environment variable called QUANTOPIAN_API_KEY.

    base_url : str, optional
        The base URL for the Aqueduct API.  Defaults to the
        FactSet Aqueduct endpoint.
    """
    if api_key is None:
        api_key = load_api_key()

    return AqueductClient(
        api_key=api_key,
        base_url=base_url
    )


class AqueductClient(object):
    """
    AqueductClient provides a convenient way to use Quantopian's
    Aqueduct API.
    """
    def __init__(self, api_key, base_url):
        self._base_url = base_url
        self._api_key = api_key

    def get_all_pipeline_executions(self):
        """
        Returns the metadata of all the pipeline executions you've run.

        Parameters
        ----------
        None

        Returns
        -------
        list
            A list of all the pipeline executions you have run.  Each execution
            is represented by a dict with id, start_date, end_date, created_at,
            status, and other properties. See `get_pipeline_execution` for
            a sample dict.
        """
        response = self._get('')
        response.raise_for_status()
        pipelines = response.json()['pipelines']
        return pipelines

    def get_pipeline_execution(self, execution_id):
        """
        Returns the metadata of a single pipeline execution.

        Parameters
        ----------
        id : str
            The id of the pipeline execution to load.

        Returns
        -------
        dict
            The metadata of the pipeline execution, containing id, start_date,
            end_date, created_at, status, and other properties.

            A sample returned dictionary looks like this:
            {
                "id": "5cdc808085835b718cdec77b"
                'status': "SUCCESS",
                "start_date": "2010-01-01",
                "end_date": "2013-01-01",
                "code": <str>,
                "created_at": '2019-05-15T21:11:28.298405",
                "params": {},
                "name": "First Pipeline Execution",
            }
        """
        response = self._get('/{execution_id}'.format(
            execution_id=execution_id
        ))
        response.raise_for_status()
        pipeline = response.json()['pipeline']
        return pipeline

    def get_pipeline_execution_quota(self):
        """
        Returns the number of currently active (queued or running)
        pipeline executions, and what the quota is.

        Parameters
        ----------
        None

        Returns
        -------
        dict: A dictionary with the following keys:
            running: int
                The number of currently active pipeline executions.
            maximum: int
                The number of pipeline executions that are queued or
                running.
        """
        response = self._get("/concurrent_executions_info")
        response.raise_for_status()
        return response.json()

    def submit_pipeline_execution(self,
                                  code,
                                  start_date,
                                  end_date,
                                  name=None,
                                  params=None,
                                  asset_identifier_format="symbol"):
        """
        Creates and queues a new pipeline execution.

        Parameters
        ----------
        code : str
            The pipeline code to run.
        start_date : date-like
            Execution start date.
        end_date : date-like
            Execution end date.
        name : str, optional
            Human-readable name of the pipeline execution.
        params : dict, optional
            Input arguments for make_pipeline method defined in code.
        asset_identifier_format : str (optional)
            The type of identifier used to uniquely identify a security.
            Valid options are "symbol", "sid", or "fsym_region_id".

        Returns
        ----------
        execution_id : str
            The ID of the newly submitted pipeline execution.
        """

        if params is None:
            params = {}

        start_date = normalize_date_input(start_date)
        end_date = normalize_date_input(end_date)

        if end_date < start_date:
            raise ValueError(
                "end_date ({end}) must be on or after start_date "
                "({start})!".format(
                    end=end_date,
                    start=start_date
                )
            )

        if asset_identifier_format not in ("symbol", "sid", "fsym_region_id"):
            raise ValueError(
                "Invalid asset_identifier_format, should be symbol, "
                "sid, or fsym_region_id."
            )

        args = {
            "code": code,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "asset_identifier_format": asset_identifier_format,
            "params": params,
            "name": name,
        }

        response = self._post('', args)

        if response.status_code == 429:
            # concurrent execution quota exceeded
            data = json.loads(response.text)
            raise ConcurrentExecutionsExceeded(
                data["current"],
                data["allowed"],
            )
        else:
            response.raise_for_status()

        created_execution_id = response.json()['pipeline_id']

        return created_execution_id

    def get_pipeline_results_dataframe(self, execution_id):
        """
        Gets the result of this pipeline in a pandas dataframe.

        Parameters
        ----------
        execution_id : str
            The id of the pipeline execution whose results should be loaded.

        Returns
        -------
        pd.DataFrame
            A dataframe holding the result, indexed by date and the
            asset identifier format (symbol, sid, or fsym_region_id)
            that this pipeline used.
        """
        pipeline_status = self.get_pipeline_execution(execution_id)
        if pipeline_status["status"] == "IN-PROGRESS":
            raise ValueError(
                "Pipeline execution {execution_id} is still running!".format(
                    execution_id=execution_id
                )
            )
        elif pipeline_status["status"] == "FAILED":
            raise ValueError(
                "Pipeline {execution_id} ended in error, use "
                "`get_pipeline_execution_error` "
                "to get its error message.".format(execution_id=execution_id)
            )

        asset_identifier_format = pipeline_status["asset_identifier_format"]

        # now that we know the pipeline isn't still running, get its results
        response = self._get('/{execution_id}/results_url'.format(
            base=self._base_url,
            execution_id=execution_id
        ))

        url = response.json()['url']

        # get the data from the url
        results_url_resp = requests.get(url)

        if results_url_resp.status_code != 200:
            raise ValueError("Could not download results from given url.")

        result_df = pd.read_csv(
            StringIO(results_url_resp.text),
            index_col=['date', asset_identifier_format],
            parse_dates=['date'],
        )

        return result_df

    def get_pipeline_execution_error(self, execution_id):
        """
        Gets the error that caused this pipeline to fail to complete
        successfully.

        Parameters
        ----------
        execution_id : str
            The id of the pipeline execution whose errors should be loaded.

        Returns
        -------
        dict
            A dictionary that can contain `date`, `name`, `message`,
            `lineno`, `method` keys.
        """
        pipeline_status = self.get_pipeline_execution(execution_id)
        if pipeline_status["status"] != "FAILED":
            raise ValueError(
                "Pipeline execution {execution_id} did not end in "
                "error!".format(execution_id=execution_id)
            )

        # get the error
        response = self._get(
            '/{execution_id}/exception'.format(execution_id=execution_id),
        )

        response.raise_for_status()

        return response.json()

    def _get(self, path):
        return requests.get(
            self._base_url + path,
            headers={'Quantopian-API-Key': self._api_key},
        )

    def _post(self, path, body):
        return requests.post(
            self._base_url + path,
            headers={'Quantopian-API-Key': self._api_key},
            json=body,
        )
