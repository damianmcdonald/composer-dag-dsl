import os
import pytest
from composer.api import api as flask_app

# Versioned, base path definition of API
API_BASE_PATH_V1 = '/api/v1'


@pytest.fixture
def app():
    yield flask_app.app


@pytest.fixture
def client(app):
    return app.test_client()


def test_get_test(app, client):
    app.testing = True
    res = client.get(f'{API_BASE_PATH_V1}/test')
    assert res.status_code == 200
    req_data = res.get_json()
    assert 'env_vars' in req_data
    assert 'PYTHONPATH' in req_data['env_vars']


def test_get_composer_config(app, client):
    app.testing = True
    res = client.get(f'{API_BASE_PATH_V1}/composer/config')
    assert res.status_code == 200
    req_data = res.get_json()
    assert 'next_actions' in req_data
    assert 'list' in req_data['next_actions']
    assert 'validate' in req_data['next_actions']
    assert 'deploy' in req_data['next_actions']
    assert 'name' in req_data['airflow_config']
    assert 'uuid' in req_data['airflow_config']
    assert 'dagGcsPrefix' in req_data['airflow_config']['config']
    assert 'dagGcsPrefix' in req_data['airflow_config']['config']
    assert 'location' in req_data['airflow_config']['config']['nodeConfig']


def test_list_dags_no_payload(app, client):
    app.testing = True
    res = client.get(f'{API_BASE_PATH_V1}/dag/list')
    assert res.status_code == 200
    req_data = res.get_json()
    assert "dag_list" in req_data
    assert len(req_data['dag_list']) > 0


def test_list_dags_with_valid_payload(app, client):
    app.testing = True

    res = client.get(
        f'{API_BASE_PATH_V1}/dag/list',
        json={
            'project_id': os.environ.get('PROJECT_ID'),
            'location': os.environ.get('GCP_LOCATION'),
            'composer_environment': os.environ.get('COMPOSER_ENVIRONMENT')
        }
    )
    assert res.status_code == 200
    req_data = res.get_json()
    assert "dag_list" in req_data
    assert 'next_actions' in req_data
    assert 'validate' in req_data['next_actions']
    assert 'deploy' in req_data['next_actions']
    assert len(req_data['dag_list']) > 0


def test_list_dags_with_invalid_payload(app, client):
    app.testing = True
    with pytest.raises(Exception):
        client.get(
            f'{API_BASE_PATH_V1}/dag/list',
            json={
                'project_id': os.environ.get('PROJECT_ID'),
                'location': os.environ.get('GCP_LOCATION')
            }
        )


def test_validate_dag_with_valid_k8s_payload(app, client):
    app.testing = True
    res = client.post(
        f'{API_BASE_PATH_V1}/dag/validate',
        json={
            'project_id': os.environ.get('PROJECT_ID'),
            'location': os.environ.get('GCP_LOCATION'),
            'composer_environment': os.environ.get('COMPOSER_ENVIRONMENT'),
            'dag_name': 'minimal_dag_kubernetes_pod_operator',
            'mode': 'INLINE',
            'kubernetes_pod_operators': [
                {
                    'task_id': 'k8s_pod_operator_example_task_01',
                    'name': 'k8s_pod_example_01',
                    'image': 'bash'
                }
            ]
        }
    )
    assert res.status_code == 200
    req_data = res.get_json()
    assert req_data is not None
    assert 'next_actions' in req_data
    assert 'deploy' in req_data['next_actions']
    assert req_data['is_valid']
    assert req_data['dag_definition'] is not None


def test_validate_dag_with_invalid_k8s_payload(app, client):
    app.testing = True
    res = client.post(
            f'{API_BASE_PATH_V1}/dag/validate',
            json={
                'dag_name': 'minimal_dag_kubernetes_pod_operator',
                'mode': 'INLINE',
                'kubernetes_pod_operators': [
                    {
                        'task_id': 'k8s_pod_operator_example_task_01',
                        'image': 'bash'
                    }
                ]
            }
        )
    assert res.status_code == 500


def test_validate_dag_with_valid_bash_payload(app, client):
    app.testing = True
    res = client.post(
        f'{API_BASE_PATH_V1}/dag/validate',
        json={
            "dag_name": "minimal_dag_bash_operator",
            'mode': 'INLINE',
            "bash_operators": [
                {
                    "task_id": "bash_operator_01",
                    "command": [
                        "echo 'Hello from Airflow Bash Operator 01'"
                    ]
                }
            ]
        }
    )
    assert res.status_code == 200
    req_data = res.get_json()
    assert req_data is not None
    assert 'next_actions' in req_data
    assert 'deploy' in req_data['next_actions']
    assert req_data['is_valid']
    assert req_data['dag_definition'] is not None


def test_validate_dag_with_invalid_bash_payload(app, client):
    app.testing = True
    res = client.post(
            f'{API_BASE_PATH_V1}/dag/validate',
            json={
                "dag_name": "minimal_dag_bash_operator",
                'mode': 'INLINE',
                "bash_operators": [
                    {
                        "task_id": "bash_operator_01",
                        "command": [
                        ]
                    }
                ]
            }
        )
    assert res.status_code == 500


def test_validate_dag_with_valid_python_payload(app, client):
    app.testing = True
    res = client.post(
        f'{API_BASE_PATH_V1}/dag/validate',
        json={
            "dag_name": "minimal_dag_python_operator",
            'mode': 'INLINE',
            "python_operators": [
                {
                    "task_id": "python_operator_01",
                    "function_def": [
                        "def python_operator_func_1():",
                        "   print('Hello from Airflow Python Operator 01 -- DYNAMIC')"
                    ],
                    "function_name": "python_operator_func_1"
                }
            ]
        }
    )
    assert res.status_code == 200
    req_data = res.get_json()
    assert req_data is not None
    assert 'next_actions' in req_data
    assert 'deploy' in req_data['next_actions']
    assert req_data['is_valid']
    assert req_data['dag_definition'] is not None


def test_validate_dag_with_invalid_python_payload(app, client):
    app.testing = True
    res = client.post(
            f'{API_BASE_PATH_V1}/dag/validate',
            json={
                "dag_name": "minimal_dag_python_operator",
                'mode': 'INLINE',
                "python_operators": [
                    {
                        "task_id": "python_operator_01",
                        "function_def": [
                            "def python_operator_func_1():",
                            "   print('Hello from Airflow Python Operator 01 -- DYNAMIC')"
                        ]
                    }
                ]
            }
        )
    assert res.status_code == 500


def test_validate_dag_with_valid_gcs_file(app, client):
    app.testing = True
    res = client.post(
            f'{API_BASE_PATH_V1}/dag/validate',
            json={
                "dag_name": "dag_workflow_simple",
                'mode': 'GCS',
                "bucket_name": os.environ.get('TEST_BUCKET'),
                "file_path": "dags/dag_workflow_simple.py"
            }
        )
    assert res.status_code == 200
    req_data = res.get_json()
    assert req_data is not None
    assert 'next_actions' in req_data
    assert 'deploy' in req_data['next_actions']
    assert req_data['is_valid']
    assert req_data['dag_definition'] is not None


def test_validate_dag_with_invalid_gcs_file(app, client):
    app.testing = True
    res = client.post(
                f'{API_BASE_PATH_V1}/dag/validate',
                json={
                    "dag_name": "dag_workflow_simple",
                    'mode': 'GCS',
                    "bucket_name": "bad_bucket",
                    "file_path": "dags/dag_workflow_simple.py"
                }
            )
    assert res.status_code == 500


def test_deploy_dag_with_valid_gcs_file(app, client):
    app.testing = True
    res = client.post(
                f'{API_BASE_PATH_V1}/dag/deploy',
                json={
                    "dag_name": "dag_workflow_simple",
                    'mode': 'GCS',
                    "bucket_name": os.environ.get('TEST_BUCKET'),
                    "file_path": "dags/dag_workflow_simple.py"
                }
            )
    assert res.status_code == 200
    req_data = res.get_json()
    assert req_data is not None
    assert 'next_actions' in req_data
    assert 'trigger' in req_data['next_actions']
    assert req_data['dag_name'] is not None
    assert req_data['dag_gcs_path'] is not None
    assert req_data['next_actions'] is not None


def test_deploy_dag_with_valid_inline(app, client):
    app.testing = True
    res = client.post(
                f'{API_BASE_PATH_V1}/dag/deploy',
                json={
                    'project_id': os.environ.get('PROJECT_ID'),
                    'location': os.environ.get('GCP_LOCATION'),
                    'composer_environment': os.environ.get('COMPOSER_ENVIRONMENT'),
                    'dag_name': 'test_gcs_deploy',
                    'mode': 'INLINE',
                    'kubernetes_pod_operators': [
                        {
                            'task_id': 'k8s_pod_operator_example_task_01',
                            'name': 'k8s_pod_example_01',
                            'image': 'bash'
                        }
                    ]
                }
            )
    assert res.status_code == 200
    req_data = res.get_json()
    assert req_data is not None
    assert 'next_actions' in req_data
    assert 'trigger' in req_data['next_actions']
    assert req_data['dag_name'] is not None
    assert req_data['dag_gcs_path'] is not None
    assert req_data['next_actions'] is not None


def test_deploy_dag_with_valid_git_file(app, client):
    app.testing = True
    res = client.post(
                f'{API_BASE_PATH_V1}/dag/deploy',
                json={
                    "dag_name": "dag_workflow_simple",
                    'mode': 'GIT',
                    "git_url": os.environ.get('TEST_GIT_URL'),
                    "repo_name": "repo-test-dir",
                    "file_path": os.environ.get('TEST_GIT_FILE_PATH')
                }
            )
    assert res.status_code == 200
    req_data = res.get_json()
    assert req_data is not None
    assert 'next_actions' in req_data
    assert 'trigger' in req_data['next_actions']
    assert req_data['dag_name'] is not None
    assert req_data['dag_gcs_path'] is not None
    assert req_data['next_actions'] is not None


def test_deploy_dag_with_invalid_git_file(app, client):
    app.testing = True
    res = client.post(
                f'{API_BASE_PATH_V1}/dag/deploy',
                json={
                    "dag_name": "dag_workflow_simple",
                    'mode': 'GIT',
                    "git_url": os.environ.get('TEST_GIT_URL'),
                    "repo_name": "repo-test-dir",
                    "file_path": "bad_path.py"
                }
            )
    assert res.status_code == 500


def test_get_composer_config(app, client):
    app.testing = True
    res = client.get(f'{API_BASE_PATH_V1}/composer/config')
    assert res.status_code == 200
    req_data = res.get_json()
    assert 'next_actions' in req_data
    assert 'list' in req_data['next_actions']
    assert 'validate' in req_data['next_actions']
    assert 'deploy' in req_data['next_actions']
    assert 'name' in req_data['airflow_config']
    assert 'uuid' in req_data['airflow_config']
    assert 'dagGcsPrefix' in req_data['airflow_config']['config']
    assert 'dagGcsPrefix' in req_data['airflow_config']['config']
    assert 'location' in req_data['airflow_config']['config']['nodeConfig']


def test_get_composer_experimental_apì(app, client):
    app.testing = True
    res = client.get(f'{API_BASE_PATH_V1}/composer/api')
    assert res.status_code == 200
    req_data = res.get_json()
    assert 'next_actions' in req_data
    assert len(req_data['next_actions']) > 0
    assert 'airflow_uri' in req_data
    assert 'client_id' in req_data


def test_trigger_dag(app, client):
    app.testing = True
    res = client.put(f'{API_BASE_PATH_V1}/dag/trigger/test_trigger_dag')
    assert res.status_code == 200
    req_data = res.get_json()
    assert req_data is not None
    assert 'api_response' in req_data
    assert 'next_actions' in req_data
    assert len(req_data['next_actions']) > 0
