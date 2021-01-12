import json
import os
from pathlib import Path
from composer.airflow import airflow_service
from unittest import TestCase, mock, main


class MockResponse:
    def __init__(self, json_data, status_code, headers, text=None):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = headers
        self.text = text

    def json(self):
        return self.json_data

    def headers(self):
        return self.headers

    def status_code(self):
        return self.status_code

    def text(self):
        return self.text


class AirflowServiceTests(TestCase):

    @mock.patch('google.auth.transport.requests.AuthorizedSession')
    @mock.patch('flask.Response')
    @mock.patch('requests.get')
    @mock.patch('six.moves.urllib.parse.parse_qs')
    def test_get_airflow_config(self, mock_six_parse, mock_requests_get, mock_flask_response, mock_auth_session):
        with open(os.path.join(os.path.dirname(Path(__file__)), 'airflow_config.json')) as json_file:
            airflow_config = json.load(json_file)

        # mock the objects
        mock_flask_response.json.return_value = airflow_config
        mock_six_parse.return_value = airflow_config['query_string']
        mock_auth_session.request.return_value = mock_flask_response
        headers = {
            'location': airflow_config['query_string']['redirect_uri'][0]
        }
        mock_requests_get.return_value = MockResponse({}, 200, headers)

        airflow_svc = airflow_service.AirflowService(
            mock_auth_session,
            os.environ.get('PROJECT_ID'),
            os.environ.get('GCP_LOCATION'),
            os.environ.get('COMPOSER_ENVIRONMENT')
        )
        composer_config = airflow_svc.get_airflow_config()
        assert composer_config is not None
        assert 'name' in composer_config
        assert composer_config['name'] == airflow_config['name']
        assert 'uuid' in composer_config
        assert composer_config['uuid'] == airflow_config['uuid']
        assert 'dagGcsPrefix' in composer_config['config']
        assert composer_config['config']['dagGcsPrefix'] == airflow_config['config']['dagGcsPrefix']
        assert 'client_id' in composer_config['query_string']
        assert composer_config['query_string']['client_id'] == airflow_config['query_string']['client_id']

    @mock.patch('google.auth.transport.requests.AuthorizedSession')
    @mock.patch('flask.Response')
    @mock.patch('requests.get')
    @mock.patch('six.moves.urllib.parse.parse_qs')
    def test_get_airflow_dag_gcs(self, mock_six_parse, mock_requests_get, mock_flask_response, mock_auth_session):
        with open(os.path.join(os.path.dirname(Path(__file__)), 'airflow_config.json')) as json_file:
            airflow_config = json.load(json_file)

        # mock the objects
        mock_flask_response.json.return_value = airflow_config
        mock_six_parse.return_value = airflow_config['query_string']
        mock_auth_session.request.return_value = mock_flask_response
        headers = {
            'location': airflow_config['query_string']['redirect_uri'][0]
        }
        mock_requests_get.return_value = MockResponse({}, 200, headers)

        airflow_svc = airflow_service.AirflowService(
            mock_auth_session,
            os.environ.get('PROJECT_ID'),
            os.environ.get('GCP_LOCATION'),
            os.environ.get('COMPOSER_ENVIRONMENT')
        )

        dag_gcs_path = airflow_svc.get_airflow_dag_gcs()
        assert dag_gcs_path is not None
        assert dag_gcs_path == 'gs://europe-west3-composer-1b28efe1-bucket/dags'

    @mock.patch('google.auth.transport.requests.AuthorizedSession')
    @mock.patch('flask.Response')
    @mock.patch('requests.get')
    @mock.patch('six.moves.urllib.parse.parse_qs')
    def test_get_airflow_experimental_api(self, mock_six_parse, mock_requests_get, mock_flask_response, mock_auth_session):
        with open(os.path.join(os.path.dirname(Path(__file__)), 'airflow_config.json')) as json_file:
            airflow_config = json.load(json_file)

        # mock the objects
        mock_flask_response.json.return_value = airflow_config
        mock_six_parse.return_value = airflow_config['query_string']
        mock_auth_session.request.return_value = mock_flask_response
        headers = {
            'location': airflow_config['query_string']['redirect_uri'][0]
        }
        mock_requests_get.return_value = MockResponse({}, 200, headers)

        airflow_svc = airflow_service.AirflowService(
            mock_auth_session,
            os.environ.get('PROJECT_ID'),
            os.environ.get('GCP_LOCATION'),
            os.environ.get('COMPOSER_ENVIRONMENT')
        )

        airflow_ui, client_id = airflow_svc.get_airflow_experimental_api()
        assert airflow_ui is not None
        assert client_id is not None
        assert airflow_ui == 'https://sde120c7fa68ea00ep-tp.appspot.com/api/experimental'
        assert client_id == '401501771865-j04v42mav328ocngb267ts6mlh82j8uk.apps.googleusercontent.com'

    @mock.patch('composer.utils.auth_service.get_id_token')
    @mock.patch('requests.request')
    def test_trigger_dag(self, mock_request, mock_auth_service):
        mock_auth_service.return_value = 'fake_id_token'
        mock_request.return_value = MockResponse({}, 200, {}, "mock_response_text")
        airflow_svc = airflow_service.AirflowService(
            'fake_auth_session',
            os.environ.get('PROJECT_ID'),
            os.environ.get('GCP_LOCATION'),
            os.environ.get('COMPOSER_ENVIRONMENT')
        )
        res_text = airflow_svc.trigger_dag('mock_dag_name', 'mock_airflow_ui', ',mock_client_id')
        assert res_text is not None
        assert res_text == "mock_response_text"


if __name__ == '__main__':
    main()
