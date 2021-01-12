import os
import time
import pytest
from pathlib import Path
from composer.api import api_service
from composer.utils import auth_service
from composer.airflow import airflow_service


def test_gcs_upload_file_temp_bucket():
    project_id, location, composer_environment = api_service.get_gcp_composer_details(None)
    bucket_name = os.environ.get('TEST_BUCKET')
    prefix = "dags/"
    upload_file = "static/dag_workflow_simple.py"
    file_path = os.path.join(os.path.dirname(Path(__file__)), upload_file)
    api_service.gcs_upload_file(project_id, bucket_name, prefix, file_path)


def test_gcs_download_file_temp_bucket():
    project_id, location, composer_environment = api_service.get_gcp_composer_details(None)
    test_gcs_upload_file_temp_bucket()
    file_path = api_service.gcs_download_file(
        project_id,
        os.environ.get('TEST_BUCKET'),
        'dags/dag_workflow_simple.py'
    )
    assert os.path.exists(file_path)
    assert os.path.isfile(file_path)
    assert not os.path.isdir(file_path)


def test_gcs_upload_file_airflow_bucket():
    project_id, location, composer_environment = api_service.get_gcp_composer_details(None)
    bucket_name = api_service.get_dag_bucket(project_id, location, composer_environment)
    prefix = "dags/"
    upload_file = "static/dag_workflow_simple.py"
    file_path = os.path.join(os.path.dirname(Path(__file__)), upload_file)
    api_service.gcs_upload_file(project_id, bucket_name, prefix, file_path)


def test_gcs_download_file_temp_bucket():
    project_id, location, composer_environment = api_service.get_gcp_composer_details(None)
    test_gcs_upload_file_airflow_bucket()
    bucket_name = api_service.get_dag_bucket(project_id, location, composer_environment)
    file_path = api_service.gcs_download_file(
        project_id,
        bucket_name,
        'dags/dag_workflow_simple.py'
    )
    assert os.path.exists(file_path)
    assert os.path.isfile(file_path)
    assert not os.path.isdir(file_path)


def test_git_download_file():
    test_git_url = os.environ.get('TEST_GIT_URL')
    test_git_file_path = os.environ.get('TEST_GIT_FILE_PATH')
    downloaded_file = api_service.git_download_file(
        test_git_url,
        "repo-test",
        test_git_file_path
    )
    assert os.path.exists(downloaded_file)
    assert os.path.isfile(downloaded_file)
    assert not os.path.isdir(downloaded_file)


# TODO - test /composer/config, /composer/api, /dag/trigger/<dag_name>, /dag/delete/<dag_name>
def test_get_gcp_composer_environment_by_valid_json():
    json = {
        'project_id': os.environ.get('PROJECT_ID'),
        'location': os.environ.get('GCP_LOCATION'),
        'composer_environment': os.environ.get('COMPOSER_ENVIRONMENT')
    }
    project_id, location, composer_environment = api_service.get_gcp_composer_details(json)
    req_data = api_service.__get_composer_environment(project_id, location, composer_environment)
    assert req_data is not None


def test_get_gcp_composer_environment_by_envvars():
    project_id, location, composer_environment = api_service.get_gcp_composer_details()
    req_data = api_service.__get_composer_environment(project_id, location, composer_environment)
    assert req_data is not None


def test_get_gcp_composer_details_by_valid_json():
    json = {
        'project_id': os.environ.get('PROJECT_ID'),
        'location': os.environ.get('GCP_LOCATION'),
        'composer_environment': os.environ.get('COMPOSER_ENVIRONMENT')
    }
    project_id, location, composer_environment = api_service.get_gcp_composer_details(json)
    assert project_id is not None
    assert project_id == os.environ.get('PROJECT_ID')
    assert location is not None
    assert location == os.environ.get('GCP_LOCATION')
    assert composer_environment is not None
    assert composer_environment == os.environ.get('COMPOSER_ENVIRONMENT')


def test_get_gcp_composer_details_by_invalid_json():
    json = {
        'project_id': os.environ.get('PROJECT_ID'),
        'location': os.environ.get('GCP_LOCATION')
    }
    with pytest.raises(Exception):
        api_service.get_gcp_composer_details(json)


def test_get_gcp_composer_details_by_env_vars():
    project_id, location, composer_environment = api_service.get_gcp_composer_details()
    assert project_id is not None
    assert project_id == os.environ.get('PROJECT_ID')
    assert location is not None
    assert location == os.environ.get('GCP_LOCATION')
    assert composer_environment is not None
    assert composer_environment == os.environ.get('COMPOSER_ENVIRONMENT')


def test_get_next_actions_experimental_api():
    authenticated_session = auth_service.get_authenticated_session()
    airflow_uri, client_id = airflow_service.AirflowService(
        authenticated_session,
        os.environ.get('PROJECT_ID'),
        os.environ.get('GCP_LOCATION'),
        os.environ.get('COMPOSER_ENVIRONMENT')
    ).get_airflow_experimental_api()
    next_actions = api_service.get_next_actions_experimental_api(airflow_uri, client_id)
    assert 'endpoints' in next_actions
    assert len(next_actions['endpoints']) > 0
    assert 'description' in next_actions['endpoints'][0]
    assert 'api_url' in next_actions['endpoints'][0]
    assert 'http_method' in next_actions['endpoints'][0]
    assert 'api_ref' in next_actions['endpoints'][0]
    assert 'client_id' in next_actions['endpoints'][0]


def test_trigger_dag():
    project_id, location, composer_environment = api_service.get_gcp_composer_details(None)
    airflow_dag_bucket_name = api_service.get_dag_bucket(project_id, location, composer_environment)
    json = {
        'project_id': os.environ.get('PROJECT_ID'),
        'location': os.environ.get('GCP_LOCATION'),
        'composer_environment': os.environ.get('COMPOSER_ENVIRONMENT'),
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
    gcs_dag_path = api_service.deploy_dag(project_id, 'INLINE', airflow_dag_bucket_name, dag_data=json)

    # sleep in order to give the dag time to deploy
    time.sleep(30)

    response_text = api_service.trigger_dag(project_id, location, composer_environment, 'test_trigger_dag')
    assert response_text is not None
