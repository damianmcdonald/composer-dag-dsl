#!/usr/bin/env python

"""airflow_service.py: Provides functionality to interact with GCP Cloud Composer (Apache Airflow)."""

__author__ = "Damian McDonald"
__credits__ = ["Damian McDonald"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Damian McDonald"
__status__ = "Development"

import requests
import logging
import six.moves.urllib.parse
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from composer.utils import auth_service, log_service


class AirflowService:

    """Class to interact with GCP Cloud Composer (Apache Airflow)"""

    IAM_SCOPE = 'https://www.googleapis.com/auth/iam'
    OAUTH_TOKEN_URI = 'https://www.googleapis.com/oauth2/v4/token'

    # gets the logger for this module
    logger = log_service.get_module_logger(__name__)

    # [START AirflowService constructor]
    def __init__(self, authenticated_session, project_id, location, composer_environment):
        """
        AirflowService constructor.
        Args:
            authenticated_session (google.auth.transport.requests.AuthorizedSession): A GCP authenticated session
            project_id (string): GCP Project Id of the Cloud Composer instance
            location (string): GCP Zone of the Cloud Composer instance
            composer_environment (string): Name of the Cloud Composer instance
        """
        self.authenticated_session = authenticated_session
        self.project_id = project_id
        self.location = location
        self.composer_environment = composer_environment
    # [END AirflowService constructor]

    # [START get_airflow_config]
    def get_airflow_config(self):
        """
        Gets the details of the Cloud Composer environment
        Returns:
            a dictionary containing the details of the Cloud Composer environment
        """
        self.logger.log(logging.DEBUG, "Entered get_airflow_config method")
        environment_url = (
            'https://composer.googleapis.com/v1beta1/projects/{}/locations/{}'
            '/environments/{}'
        ).format(
            self.project_id,
            self.location,
            self.composer_environment
        )
        self.logger.log(logging.DEBUG, f"Cloud Composer environment URL: {environment_url}")
        composer_response = self.authenticated_session.request('GET', environment_url)
        environment_data = composer_response.json()
        airflow_uri = environment_data['config']['airflowUri']

        # The Composer environment response does not include the IAP client ID.
        # Make a second, unauthenticated HTTP request to the web server to get the
        # redirect URI.
        redirect_response = requests.get(airflow_uri, allow_redirects=False)
        redirect_location = redirect_response.headers['location']

        # Extract the client_id query parameter from the redirect.
        parsed = six.moves.urllib.parse.urlparse(redirect_location)
        query_string = six.moves.urllib.parse.parse_qs(parsed.query)
        environment_data['query_string'] = query_string
        return environment_data
    # [END get_airflow_config]

    # [START get_airflow_experimental_api]
    def get_airflow_experimental_api(self):
        """
        Gets the details of the Cloud Composer experimental API
        Returns:
            a tuple containing the airflow experimental api uri path and airflow client id
        """
        self.logger.log(logging.DEBUG, "Entered get_airflow_experimental_api method")
        environment_data = self.get_airflow_config()
        airflow_uri = environment_data['config']['airflowUri']
        client_id = environment_data['query_string']['client_id'][0]
        return f"{airflow_uri}/api/experimental", client_id
    # [END get_airflow_experimental_api]

    # [START get_airflow_dag_gcs]
    def get_airflow_dag_gcs(self):
        """
        Gets the Google Cloud Storage path for the dag files in the Cloud Composer environment
        Returns:
            the name of the Cloud Composer Google Cloud Storage dag file bucket
        """
        self.logger.log(logging.DEBUG, "Entered get_airflow_dag_gcs method")
        environment_data = self.get_airflow_config()
        self.logger.log(
            logging.INFO,
            f"Google Cloud Storage path for the dag files: {environment_data['config']['dagGcsPrefix']}"
        )
        return environment_data['config']['dagGcsPrefix']
    # [END get_airflow_dag_gcs]

    # [START trigger_dag]
    def trigger_dag(self, dag_name, airflow_uri, client_id, data=None):
        """
        Makes a POST request to the Cloud Composer experimental API to trigger a DAG
        Returns:
            the page body, or raises an exception if the page couldn't be retrieved.
        """
        self.logger.log(logging.DEBUG, "Entered trigger_dag method")
        self.logger.log(
            logging.DEBUG,
            f"trigger_dag method params. dag_name: {dag_name}, airflow_uri: {airflow_uri}, client_id: {client_id}, data: {data}"
        )
        webserver_url = f"{airflow_uri}/dags/{dag_name}/dag_runs"
        self.logger.log(logging.INFO, f"Web server URL: {webserver_url}")
        # Make a POST request to IAP which then Triggers the DAG
        if data:
            return self.make_post_iap_request(webserver_url, client_id, {"conf": data})
        else:
            return self.make_post_iap_request(webserver_url, client_id, {})
    # [END trigger_dag]

    # [START make_post_iap_request]
    # This code is copied from
    # https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/iap/make_iap_request.py
    # START COPIED IAP CODE
    def make_post_iap_request(self, url, client_id, json, **kwargs):
        """Makes a POST request to an application protected by Identity-Aware Proxy.
        Args:
          url: The Identity-Aware Proxy-protected URL to fetch.
          client_id: The client ID used by Identity-Aware Proxy.
          json: A JSON payload containing any additional data to be included with the POST request.
          **kwargs: Any of the parameters defined for the request function:
                    https://github.com/requests/requests/blob/master/requests/api.py
                    If no timeout is provided, it is set to 90 by default.
        Returns:
          The page body, or raises an exception if the page couldn't be retrieved.
        """

        self.logger.log(logging.DEBUG, "Entered make_post_iap_request method")
        self.logger.log(
            logging.DEBUG,
            f"make_post_iap_request method params. url: {url}, client_id: {client_id}, json: {json}"
        )

        # Set the default timeout, if missing
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 90

        # Obtain an OpenID Connect (OIDC) token from metadata server or using service
        # account.

        # try to get the id token from the auth_service
        google_open_id_connect_token = auth_service.get_id_token(Request(), client_id)
        if google_open_id_connect_token is None:
            google_open_id_connect_token = id_token.fetch_id_token(Request(), client_id)

        # Fetch the Identity-Aware Proxy-protected URL, including an
        # Authorization header containing "Bearer " followed by a
        # Google-issued OpenID Connect token for the service account.
        resp = requests.request(
            'POST', url,
            headers={
                'Authorization': 'Bearer {}'.format(google_open_id_connect_token),
                'Content-Type': 'application/json'
            },
            json=json,
            **kwargs
        )
        if resp.status_code == 403:
            raise Exception('Service account does not have permission to '
                            'access the IAP-protected application.')
        elif resp.status_code != 200:
            raise Exception(
                'Bad response from application: {!r} / {!r} / {!r}'.format(
                    resp.status_code, resp.headers, resp.text))
        else:
            return resp.text
    # END COPIED IAP CODE
    # [END make_post_iap_request]

    # [START make_get_iap_request]
    # This code is copied from
    # https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/iap/make_iap_request.py
    # START COPIED IAP CODE
    def make_get_iap_request(self, url, client_id, **kwargs):
        """Makes a GET request to an application protected by Identity-Aware Proxy.
        Args:
          url: The Identity-Aware Proxy-protected URL to fetch.
          client_id: The client ID used by Identity-Aware Proxy.
          **kwargs: Any of the parameters defined for the request function:
                    https://github.com/requests/requests/blob/master/requests/api.py
                    If no timeout is provided, it is set to 90 by default.
        Returns:
          The page body, or raises an exception if the page couldn't be retrieved.
        """

        self.logger.log(logging.DEBUG, "Entered make_get_iap_request method")
        self.logger.log(
            logging.DEBUG,
            f"make_get_iap_request method params. url: {url}, client_id: {client_id}"
        )

        # Set the default timeout, if missing
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 90

        # try to get the id token from the auth_service
        google_open_id_connect_token = auth_service.get_id_token(Request(), client_id)
        if google_open_id_connect_token is None:
            google_open_id_connect_token = id_token.fetch_id_token(Request(), client_id)

        resp = requests.request(
            'GET', url,
            headers={
                'Authorization': 'Bearer {}'.format(google_open_id_connect_token)
            },
            **kwargs
        )
        if resp.status_code == 403:
            raise Exception('Service account does not have permission to '
                            'access the IAP-protected application.')
        elif resp.status_code != 200:
            raise Exception(
                'Bad response from application: {!r} / {!r} / {!r}'.format(
                    resp.status_code, resp.headers, resp.text))
        else:
            return resp.text
    # END COPIED IAP CODE
    # [END make_get_iap_request]
