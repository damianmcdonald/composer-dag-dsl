import pytest
from unittest import TestCase, main
from composer.api import api_validator


class ApiValidatorTests(TestCase):

    @staticmethod
    def test_validate_project_json_valid():
        json = {
            'project_id': 'mock_project_id',
            'location': 'mock_gcp_location',
            'composer_environment': 'mock_composer_environment'
        }
        is_valid = api_validator.validate_project_json(json)
        assert is_valid

    @staticmethod
    def test_validate_project_json_missing_project_id():
        json = {
            'location': 'mock_gcp_location',
            'composer_environment': 'mock_composer_environment'
        }
        with pytest.raises(ValueError):
            api_validator.validate_project_json(json)

    @staticmethod
    def test_validate_project_json_missing_location():
        json = {
            'project_id': 'mock_project_id',
            'composer_environment': 'mock_composer_environment'
        }
        with pytest.raises(ValueError):
            api_validator.validate_project_json(json)

    @staticmethod
    def test_validate_project_json_missing_composer_environment():
        json = {
            'project_id': 'mock_project_id',
            'location': 'mock_gcp_location',
        }
        with pytest.raises(ValueError):
            api_validator.validate_project_json(json)

    @staticmethod
    def test_validate_payload_inline_valid():
        json = {
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
        is_valid = api_validator.validate_payload(json)
        assert is_valid

    @staticmethod
    def test_validate_payload_gcs_valid():
        json = {
            'project_id': 'mock_project_id',
            'location': 'mock_gcp_location',
            'composer_environment': 'mock_composer_environment',
            'dag_name': 'test_trigger_dag',
            'mode': 'GCS',
            'bucket_name': 'mock_bucket_name',
            'file_path': 'dags/dag_workflow_simple.py'
        }
        is_valid = api_validator.validate_payload(json)
        assert is_valid

    @staticmethod
    def test_validate_payload_git_valid():
        json = {
            'project_id': 'mock_project_id',
            'location': 'mock_gcp_location',
            'composer_environment': 'mock_composer_environment',
            'dag_name': 'test_trigger_dag',
            'mode': 'GIT',
            'git_url': 'path.to.git.repo',
            'repo_name': 'repo-test-dir',
            'file_path': 'mock/path/to/dag.py'
        }
        is_valid = api_validator.validate_payload(json)
        assert is_valid

    @staticmethod
    def test_validate_payload_inline_invalid():
        json = {
            'project_id': 'mock_project_id',
            'location': 'mock_gcp_location',
            'composer_environment': 'mock_composer_environment',
            'dag_name': 'test_trigger_dag',
            'mode': 'INLINE',
            'kubernetes_pod_operators': [
                {
                    'task_id': 'k8s_pod_operator_example_task_01',
                    'name': 'k8s_pod_example_01'
                }
            ]
        }
        with pytest.raises(ValueError):
            api_validator.validate_payload(json)

    @staticmethod
    def test_validate_payload_gcs_invalid():
        json = {
            'project_id': 'mock_project_id',
            'location': 'mock_gcp_location',
            'composer_environment': 'mock_composer_environment',
            'dag_name': 'test_trigger_dag',
            'mode': 'GCS',
            'file_path': 'dags/dag_workflow_simple.py'
        }
        with pytest.raises(ValueError):
            api_validator.validate_payload(json)

    @staticmethod
    def test_validate_payload_git_invalid():
        json = {
            'project_id': 'mock_project_id',
            'location': 'mock_gcp_location',
            'composer_environment': 'mock_composer_environment',
            'dag_name': 'test_trigger_dag',
            'mode': 'GIT',
            'git_url': 'path.to.git.repo',
            'file_path': 'mock/path/to/dag.py'
        }
        with pytest.raises(ValueError):
            api_validator.validate_payload(json)


if __name__ == '__main__':
    main()
