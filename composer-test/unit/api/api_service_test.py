import json
import os
import pytest
from pathlib import Path
from unittest import TestCase, main, mock
from composer.api import api_service


class ApiServiceTests(TestCase):

    @mock.patch('composer.utils.auth_service.get_credentials')
    @mock.patch('composer.airflow.airflow_service.AirflowService.get_airflow_config')
    def test_get_dag_bucket(self, mock_get_airflow_config, mock_get_credentials):
        with open(os.path.join(os.path.dirname(Path(__file__)), 'airflow_config.json')) as json_file:
            airflow_config = json.load(json_file)

        mock_get_credentials.return_value = "mock_credentials"
        mock_get_airflow_config.return_value = airflow_config
        bucket_name = api_service.get_dag_bucket(
            'mock_project_id',
            'mock_gcp_location',
            'mock_composer_environment'
        )
        assert bucket_name is not None
        assert bucket_name == 'europe-west3-composer-1b28efe1-bucket'

    @staticmethod
    def test_validate_dag_inline_valid():
        payload = {
            'project_id': 'mock_project_id',
            'location': 'mock_gcp_location',
            'composer_environment': 'mock_composer_environment',
            'dag_name': 'test_trigger_dag',
            'mode': 'INLINE',
            'kubernetes_pod_operators': [
                {
                    'task_id': 'k8s_pod_operator_example_task_01',
                    'name': 'k8s_pod_example_01',
                    'image': 'bash'
                }
            ]
        }
        dag_details = api_service.validate_dag('INLINE', payload)
        assert dag_details is not None
        assert 'is_valid' in dag_details
        assert 'dag_definition' in dag_details

    @staticmethod
    def test_validate_dag_gcs_valid():
        test_dag = os.path.join(os.path.dirname(Path(__file__)), 'static', 'dag_workflow_simple.py')
        dag_details = api_service.validate_dag('GCS', test_dag)
        assert dag_details is not None
        assert 'is_valid' in dag_details
        assert 'dag_definition' in dag_details

    @staticmethod
    def test_validate_dag_git_valid():
        test_dag = os.path.join(os.path.dirname(Path(__file__)), 'static', 'dag_workflow_simple.py')
        dag_details = api_service.validate_dag('GIT', test_dag)
        assert dag_details is not None
        assert 'is_valid' in dag_details
        assert 'dag_definition' in dag_details

    @staticmethod
    def test_validate_dag_inline_invalid():
        payload = {
            'project_id': 'mock_project_id',
            'location': 'mock_gcp_location',
            'composer_environment': 'mock_composer_environment',
            'dag_name': 'test_trigger_dag',
            'mode': 'INLINE',
            'kubernetes_pod_operators': [
                {
                    'task_id': 'k8s_pod_operator_example_task_01',
                    'name': 'k8s_pod_example_01',
                }
            ]
        }
        with pytest.raises(Exception):
            api_service.validate_dag('INLINE', payload)

    @staticmethod
    def test_validate_dag_gcs_invalid():
        with pytest.raises(Exception):
            api_service.validate_dag('GCS', '/non/valid/dag/path.py')

    @staticmethod
    def test_validate_dag_git_invalid():
        with pytest.raises(Exception):
            api_service.validate_dag('GIT', '/non/valid/dag/path.py')

    @staticmethod
    def test_get_next_actions_experimental_api():
        next_actions = api_service.get_next_actions_experimental_api('airflow_uri', 'client_id')
        assert next_actions is not None
        assert 'api_ref' in next_actions
        assert next_actions['api_ref'] == 'https://airflow.apache.org/docs/apache-airflow/stable/rest-api-ref.html'
        assert 'endpoints' in next_actions
        assert len(next_actions['endpoints']) == 12
        assert 'description' in next_actions['endpoints'][0]
        assert next_actions['endpoints'][0]['description'] == 'Creates a dag_run for a given dag id'
        assert 'api_url' in next_actions['endpoints'][0]
        assert next_actions['endpoints'][0]['api_url'] == 'airflow_uri/dags/<DAG_ID>/dag_runs'
        assert 'http_method' in next_actions['endpoints'][0]
        assert next_actions['endpoints'][0]['http_method'] == 'POST'
        assert 'api_ref' in next_actions['endpoints'][0]
        assert next_actions['endpoints'][0]['api_ref'] == 'https://airflow.apache.org/docs/apache-airflow/stable/rest-api-ref.html#post--api-experimental-dags--DAG_ID--dag_runs'
        assert 'client_id' in next_actions['endpoints'][0]
        assert next_actions['endpoints'][0]['client_id'] == 'client_id'

    @staticmethod
    def test_get_gcp_composer_details_inline_valid():
        payload = {
            'project_id': 'mock_project_id',
            'location': 'mock_gcp_location',
            'composer_environment': 'mock_composer_environment'
        }
        is_valid = api_service.get_gcp_composer_details(payload)
        assert is_valid

    @staticmethod
    def test_get_gcp_composer_details_inline_invalid():
        payload = {
            'project_id': 'mock_project_id',
            'composer_environment': 'mock_composer_environment'
        }
        with pytest.raises(Exception):
            api_service.get_gcp_composer_details(payload)

    @staticmethod
    def test_get_gcp_composer_details_env_var_valid():
        os.environ['PROJECT_ID'] = 'mock_project_id'
        os.environ['GCP_LOCATION'] = 'mock_location'
        os.environ['COMPOSER_ENVIRONMENT'] = 'mock_composer_env'
        is_valid = api_service.get_gcp_composer_details()
        assert is_valid


if __name__ == '__main__':
    main()
