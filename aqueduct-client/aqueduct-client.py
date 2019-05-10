import requests
import pandas as pd

import datetime

from .utils import load_api_key


class AqueductClient(object):
    def __init__(self, api_key_param=None, base_url=None):
        if base_url:
            self._base_url = base_url
        else:
            self._base_url = \
                "https://factset.quantopian.com/api/experimental/pipelines"

        if api_key_param:
            self._api_key = api_key_param
        else:
            self._api_key = load_api_key()

        if self._api_key is None:
            raise ValueError("No API key found!")


    def get_all_pipelines(self):
        """
        Returns the metadata of all the pipelines you've run.

        Returns:
        [
            {
                'id' : 'pipeline_oid_2',
                'name' : 'More advanced pipeline execution',
                'start_date' : '2018-01-02',
                'end_date' : '2019-01-02',
                'created_at' : '2019-01-28T18:34:09.239278',
                'asset_identifier_format': 'symbol',
                'status' : 'FAILED',
            },
            {
                'id' : 'pipeline_oid_1',
                'name' : 'Example pipeline execution',
                'start_date' : '2018-01-02',
                'end_date' : '2019-01-02',
                'created_at' : '2019-01-28T18:34:09.239278',
                'asset_identifier_format': 'symbol',
                'status' : 'SUCCESS',
            },
            ...
        ]
        """
        response = self._get('', None)
        response.raise_for_status()
        pipelines = response.json()['pipelines']
        return pipelines

    def get_pipeline(self, id):
        """
        Returns the metadata of a single pipeline.

        Returns:
        {
            'id' : 'pipeline_oid_2',
            'name' : 'More advanced pipeline execution',
            'start_date' : '2018-01-02',
            'end_date' : '2019-01-02',
            'created_at' : '2019-01-28T18:34:09.239278',
            'asset_identifier_format': 'symbol',
            'status' : 'FAILED',
        },
        """
        response = self._get('/{id}'.format(id=id), None)
        response.raise_for_status()
        pipeline = response.json()['pipeline']
        return pipeline

    def create_new_pipeline(self,
                            code,
                            start_date,
                            end_date,
                            name=None,
                            params={},
                            asset_identifier_format="symbol"):
        """
        Creates and queues a new pipeline execution.

        Parameters
        ----------
        code : str
            The pipeline code to run.
        start_date : str
            Execution start date, in YYYY-MM-DD format.
        end_date : str
            Execution end date, in YYYY-MM-DD format.
        name : str (optional)
            Human-readable name of the pipeline execution.
        params : str (optional)
            Input arguments for make_pipeline method defined in code.
        asset_identifier_format : str (optional)
            The type of identifier used to uniquely identify a security.
            Valid options are "symbol", "sid", or "fsym_region_id".

        Returns
        ----------
        {
            "pipeline_id": str
        }
        """

        try:
            datetime.datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError(
                "Incorrect start date format, should be YYYY-MM-DD"
            )

        try:
            datetime.datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError(
                "Incorrect end date format, should be YYYY-MM-DD"
            )

        if asset_identifier_format not in ["symbol", "sid", "fsym_region_id"]:
            raise ValueError(
                "Invalid asset_identifier_format, should be symbol, "
                "sid, or fsym_region_id."
            )

        args = {
            "code": code,
            "start_date": start_date,
            "end_date": end_date,
            "asset_identifier_format": asset_identifier_format,
            "params": params,
            "name": name,
        }

        response = self._post('', args)
        response.raise_for_status()
        created_pipeline_id = response.json()['pipeline_id']

        return created_pipeline_id

    def get_results_dataframe(self, id):
        """
        Gets the result of this pipeline in a pandas dataframe.

        Parameters
        ----------
        id : str
            The id of the pipeline whose results should be loaded.

        Returns
        -------
        pd.DataFrame
            A dataframe holding the result, indexed by date and the
            asset identifier format (symbol, sid, or fsym_region_id)
            that this pipeline used.
        """
        pipeline_status = self.get_pipeline(id)
        if pipeline_status["status"] == "RUNNING":
            raise ValueError("Pipeline {id} is still running!".format(id=id))
        elif pipeline_status["status"] == "FAILED":
            raise ValueError(
                "Pipeline {id} ended in error, use `get_error` "
                "to get its error message."
            )

        asset_identifier_format = pipeline_status["asset_identifier_format"]

        # now that we know the pipeline isn't still running, get its results
        response = self._get('/{id}/results_url'.format(
            base=self._base_url,
            id=id
        ), None)
        response.raise_for_status()

        url = response.json()['url']

        # get the data from the url
        results_url_resp = requests.get(url)

        if results_url_resp.status_code != 200:
            raise ValueError("Could not download results from given url.")

        result_df = pd.read_csv(
            pd.compat.StringIO(results_url_resp.text),
            index_col=['date', asset_identifier_format],
        )

        return result_df

    def get_error(self, id):
        """
        Gets the error that caused this pipeline to fail to complete
        successfully.

        Parameters
        ----------
        id : str
            The id of the pipeline whose errors should be loaded.

        Returns
        -------
        dict
            A dictionary that can contain `date`, `name`, `message`,
            `lineno`, `method` keys.
        """
        pipeline_status = self.get_pipeline(id)
        if pipeline_status["status"] != "FAILED":
            raise ValueError(
                "Pipeline {id} did not end in error!"
            ).format(id=id)

        # get the error
        response = self._get(
            '/pipelines/{id}/exception'.format(id=id),
            None
        )

        response.raise_for_status()

        response_json = response.json()
        return response_json["data"]

    def _get(self, path, body, *args, **kwargs):
        return requests.get(
            self._base_url + path,
            *args,
            headers={'Quantopian-API-Key': self._api_key},
            params=body,
            **kwargs
        )

    def _post(self, path, body, *args, **kwargs):
        return requests.post(
            self._base_url + path,
            *args,
            headers={'Quantopian-API-Key': self._api_key},
            json=body,
            **kwargs
        )
