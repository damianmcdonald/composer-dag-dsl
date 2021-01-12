#!/usr/bin/env python

"""api_service.py: Service module containing functionalities for validating, generating and deploying DAG files into
           a GCP Cloud Composer (Apache Airflow)."""

__author__ = "Damian McDonald"
__credits__ = ["Damian McDonald"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Damian McDonald"
__status__ = "Development"

import logging
import re
import os
import tempfile
import shutil
import stat
import json
from git import Repo
from google.cloud import storage
from composer.utils import log_service, auth_service
from composer.airflow import airflow_service
from composer.dag import dag_validator, dag_generator

# gets the logger for this module
logger = log_service.get_module_logger(__name__)


# [START __get_composer_environment]
def __get_composer_environment(project_id, location, composer_environment):
    """
    Gets the configuration information for a Cloud Composer environment.
    Args:
        project_id (string): GCP Project Id of the Cloud Composer instance
        location (string): GCP Zone of the Cloud Composer instance
        composer_environment (string): Name of the Cloud Composer instance
    Returns:
        an instance of composer.airflow.AirflowService
    """
    logger.log(logging.DEBUG, "Getting the composer environment")
    authenticated_session = auth_service.get_authenticated_session()
    return airflow_service.AirflowService(
        authenticated_session,
        project_id,
        location,
        composer_environment
    )
# [END __get_composer_environment]


# [START get_dag_bucket]
def get_dag_bucket(project_id, location, composer_environment):
    """
    Gets the Cloud Storage bucket location for the dags in a Cloud Composer environment.
    Args:
        project_id (string): GCP Project Id of the Cloud Composer instance
        location (string): GCP Zone of the Cloud Composer instance
        composer_environment (string): Name of the Cloud Composer instance
    Returns:
        the name of the GCS bucket containing the Cloud Composer dag files
    """
    logger.log(logging.DEBUG, "Getting the DAG GCS Bucket")
    gcs_dag_bucket = __get_composer_environment(
        project_id,
        location,
        composer_environment
    ).get_airflow_dag_gcs()
    logger.log(logging.DEBUG, f"DAG GCS Bucket: {gcs_dag_bucket}")
    bucket_name = re.findall(r"(?<=\/\/)(.*?)(?=\/)", gcs_dag_bucket)
    if not bucket_name or len(bucket_name) > 1:
        raise ValueError(f"Bucket name can not be parsed: {gcs_dag_bucket}")
    logger.log(logging.DEBUG, f"DAG GCS Bucket name: {bucket_name[0]}")
    return bucket_name[0]
# [END get_dag_bucket]


# [START list_dags]
def list_dags(project_id, bucket_name):
    """
    Lists the dag files contained in the Cloud Storage bucket location of a Cloud Composer environment.
    Args:
        project_id (string): GCP Project Id of the Cloud Composer instance
        bucket_name (string): The bucket name of the GCS location of the Cloud Composer dag files
                              (without the /dags prefix)
    Returns:
        a list of dag files contained in the Cloud Storage bucket location of a Cloud Composer environment
    """
    logger.log(logging.DEBUG, "Listing the dags")
    credentials = auth_service.get_credentials()
    client = storage.Client(project_id, credentials=credentials)
    blobs = client.list_blobs(bucket_name, prefix="dags")
    dag_list = []
    for blob in blobs:
        if blob.name.endswith(".py"):
            dag_name = blob.name.replace("dags/", "").replace(".py", "")
            dag_list.append(dag_name)
    return dag_list
# [END list_dags]


# [START validate_dag]
def validate_dag(mode, dag_data):
    """
    Validates a dag file to confirm that it is valid and compatible with Cloud Composer.
    Args:
        mode (string): INLINE, GCS or GIT
        dag_data (string): Either a JSON payload containing the DSL dag definition (mode==INLINE)
                           or the path to a dag file (mode!=INLINE)
    Returns:
        a dict containing the dag_definition and an is_valid indication
    """
    logger.log(logging.DEBUG, f"Validating dag in mode: {mode} with data {dag_data}")
    if mode == "INLINE":
        dag = __construct_dag_from_dsl(dag_data)
        dag_val = dag_validator.DagValidator(dag['dag_file'])
    else:
        dag_val = dag_validator.DagValidator(dag_data)

    dag_details = {
        'is_valid': True,
        'dag_definition': json.loads(dag_val.inspect_dag()),
    }
    return dag_details
# [END validate_dag]


# [START deploy_dag]
def deploy_dag(project_id, mode, bucket_name, dag_data=None, dag_file=None):
    """
    Deploys a dag file into a Cloud Composer environment.
    Args:
        project_id (string): GCP Project Id of the Cloud Composer instance
        mode (string): INLINE, GCS or GIT
        bucket_name (string): The bucket name of the GCS location of the Cloud Composer dag files
                              (without the /dags prefix)
        dag_data (string): JSON payload containing the DSL dag definition (mode==INLINE)
        dag_file (string): Path to a dag file (mode!=INLINE)
    Returns:
        the url to the GCS bucket (gs:// path) where the dag file was deployed
    """
    logger.log(logging.DEBUG, f"Validating dag in mode: {mode}")
    if mode == "INLINE":
        if dag_data is None:
            raise ValueError(f"INLINE mode has been specified but no dag_data was provided")
        else:
            dag = __construct_dag_from_dsl(dag_data)
            # validate the dag so we don't deploy a dag with errors
            dag_validator.DagValidator(dag['dag_file']).validate_dag()
            # upload the DAG and its associated JSON payload
            gcs_upload_file(project_id, bucket_name, "dags/", dag['dag_file'])
            gcs_upload_file(project_id, bucket_name, "dags/", dag['json_file'])
            # return the GCS path
            return f"gs://{bucket_name}/dags/{os.path.basename(os.path.normpath(dag['dag_file']))}"
    else:
        if dag_file is None:
            raise ValueError(f"GCS mode has been specified but no dag_file was provided")
        else:
            # validate the dag so we don't deploy a dag with errors
            dag_validator.DagValidator(dag_file).validate_dag()
            # upload the DAG
            gcs_upload_file(project_id, bucket_name, "dags/", dag_file)
            # return the GCS path
            return f"gs://{bucket_name}/dags/{os.path.basename(os.path.normpath(dag_file))}"
# [END deploy_dag]


# [START deploy_dag]
def trigger_dag(project_id, location, composer_environment, dag_name, data=None):
    """
    Triggers an existing, specific dag file within a Cloud Composer environment.
    Args:
        project_id (string): GCP Project Id of the Cloud Composer instance
        location (string): GCP Zone of the Cloud Composer instance
        composer_environment (string): Name of the Cloud Composer instance
        dag_name (string): Name of the dag file to be triggered
        data (string): Optional JSON payload containing additional parameters to be passed to the triggered dag
    Returns:
        the response from the Cloud Composer environment
    """
    logger.log(logging.DEBUG, f"Triggering dag: {dag_name}")
    airflow = __get_composer_environment(
        project_id,
        location,
        composer_environment
    )
    airflow_uri, client_id = airflow.get_airflow_experimental_api()
    return airflow.trigger_dag(dag_name, airflow_uri, client_id, data)
# [END deploy_dag]


# [START gcs_download_file]
def gcs_download_file(project_id, bucket_name, download_file):
    """
    Downloads a dag file from a GCS bucket.
    Args:
        project_id (string): GCP Project Id of the Cloud Composer instance
        bucket_name (string): The name of the bucket (including any prefixes) where the dag is located
        download_file (string): Name of the dag file to be downloaded
    Returns:
        the absolute file path to the downloaded file
    """
    logger.log(
        logging.DEBUG,
        f"Downloading dag from GCS: project_id {project_id}, bucket_name {bucket_name}, download_file {download_file}"
    )
    credentials = auth_service.get_credentials()
    client = storage.Client(project_id, credentials=credentials)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(download_file)
    temp_dir = tempfile.gettempdir()
    download_file_path = os.path.join(temp_dir, f"{os.path.basename(os.path.normpath(download_file))}")
    logger.log(logging.DEBUG, f"Local download path: {download_file_path}")
    blob.download_to_filename(download_file_path)
    return download_file_path
# [END gcs_download_file]


# [START gcs_upload_file]
def gcs_upload_file(project_id, bucket_name, prefix, upload_file):
    """
    Uploads a dag file to a GCS bucket.
    Args:
        project_id (string): GCP Project Id of the Cloud Composer instance
        bucket_name (string): The name of the bucket (excluding any prefixes) where the dag is to be uploaded
        prefix (string): The prefix of the GCS bucket where the dag is to be uploaded
        upload_file (string): Path to the dag file to be uploaded
    """
    logger.log(
        logging.DEBUG,
        f"Upload dag to GCS: project_id {project_id}, bucket_name {bucket_name}, prefix {prefix}, upload_file {upload_file}"
    )
    credentials = auth_service.get_credentials()
    client = storage.Client(project_id, credentials=credentials)
    bucket = client.bucket(bucket_name)
    upload_file_name = os.path.basename(os.path.normpath(upload_file))
    blob = bucket.blob(prefix + upload_file_name)
    blob.upload_from_filename(upload_file)
# [END gcs_upload_file]


# [START git_download_file]
def git_download_file(git_url, repo_dir, file_path):
    """
    Uploads a dag file to a GCS bucket.
    Args:
        git_url (string): URL of the GIT repo (not including the protocol - excluding https://)
        repo_dir (string): The name of the repository (project slug)
        file_path (string): The relative path within the GIT repo where the dag is located
    Returns:
        the absolute path to the downloaded file
    """
    if os.environ.get('GIT_USERNAME') and os.environ.get('GIT_PASSWORD'):
        git_username = os.environ.get('GIT_USERNAME')
        git_username = os.environ.get('GIT_PASSWORD')
        remote = f"https://{git_username}:{git_username}@{git_url}"
    else:
        remote = f"https://{git_url}"
    temp_dir = tempfile.gettempdir()
    repo_path = os.path.join(temp_dir, repo_dir)
    # delete existing local repo if exists
    # we need to set write permissions on temp files in order to delete them
    if os.path.exists(repo_path):
        if os.path.isdir(repo_path):
            for root, dirs, files in os.walk(repo_path):
                for fname in files:
                    full_path = os.path.join(root, fname)
                    os.chmod(full_path, stat.S_IWRITE)
            shutil.rmtree(repo_path)
    Repo.clone_from(remote, repo_path)
    return os.path.join(repo_path, file_path)
# [END git_download_file]


# [START get_gcp_composer_details]
def get_gcp_composer_details(project_json=None):
    """
    Determines the details of a Cloud Composer environment based on details specifically included
    within a JSON payload or via pre-defined environment variables.
    Args:
        project_json (string): Optional JSON payload which includes
        a project_id, location and composer_environment elements
    Returns:
        a tuple containing project_id, location, composer_environment
    """
    if project_json:
        if "project_id" not in project_json:
            raise ValueError(f"Json payload provided but it does not contain 'project_id': {project_json}")
        else:
            project_id = project_json['project_id']
        if "location" not in project_json:
            raise ValueError(f"Json payload provided but it does not contain 'location': {project_json}")
        else:
            location = project_json['location']
        if "composer_environment" not in project_json:
            raise ValueError(f"Json payload provided but it does not contain 'composer_environment': {project_json}")
        else:
            composer_environment = project_json['composer_environment']
        return project_id, location, composer_environment
    else:
        if os.environ['PROJECT_ID']:
            logger.log(
                logging.DEBUG,
                f"Using env var PROJECT_ID: {os.environ['PROJECT_ID']}."
            )
            project_id = os.environ['PROJECT_ID']
        else:
            logger.log(
                logging.DEBUG,
                "Neither PROJECT_ID env var nor json payload project_id were defined."
            )
            raise ValueError("Neither PROJECT_ID env var nor json payload project_id were defined.")

        if os.environ['GCP_LOCATION']:
            logger.log(
                logging.DEBUG,
                f"Using env var GCP_LOCATION: {os.environ['GCP_LOCATION']}."
            )
            location = os.environ['GCP_LOCATION']
        else:
            logger.log(
                logging.DEBUG,
                "Neither GCP_LOCATION env var nor json payload project_id were defined."
            )
            raise ValueError(f"Neither GCP_LOCATION env var nor json payload project_id were defined.")

        if os.environ['COMPOSER_ENVIRONMENT']:
            logger.log(
                logging.DEBUG,
                f"Using env var COMPOSER_ENVIRONMENT: {os.environ['COMPOSER_ENVIRONMENT']}."
            )
            composer_environment = os.environ['COMPOSER_ENVIRONMENT']
        else:
            logger.log(
                logging.DEBUG,
                "Neither COMPOSER_ENVIRONMENT env var nor json payload project_id were defined."
            )
            raise ValueError(
                f"Neither COMPOSER_ENVIRONMENT env var nor json payload project_id were defined.")
        return project_id, location, composer_environment
# [END get_gcp_composer_details]


# [START __construct_dag_from_dsl]
def __construct_dag_from_dsl(json_dsl):
    """
    Generates a dag file from a JSON DSL payload
    Args:
        json_dsl (string): Definition of a dag file using the JSON DSL
    Returns:
        a tuple containing the absolute path to the dag_file and json_file
    """
    return dag_generator.DagGenerator(json_dsl).generate_dag()
# [END __construct_dag_from_dsl]


# [START get_next_actions_experimental_api]
def get_next_actions_experimental_api(airflow_uri, client_id):
    """
    Gets details of the Apache Airflow experimental API
    Args:
        airflow_uri (string): The URL of the Cloud Composer UI
        client_id (string): The Cloud Composer client id
    Returns:
        a dictionary containing the details of the Apache Airflow experimental API
    """
    return {
        'api_ref': 'https://airflow.apache.org/docs/apache-airflow/stable/rest-api-ref.html',
        'endpoints': [
            {
                'description': 'Creates a dag_run for a given dag id',
                'api_url': f'{airflow_uri}/dags/<DAG_ID>/dag_runs',
                'http_method': 'POST',
                'api_ref': 'https://airflow.apache.org/docs/apache-airflow/stable/rest-api-ref.html#post--api-experimental-dags--DAG_ID--dag_runs',
                "client_id": client_id
            },
            {
                'description': 'Returns a list of Dag Runs for a specific DAG ID',
                'api_url': f'{airflow_uri}/dags/<DAG_ID>/dag_runs',
                'http_method': 'GET',
                'api_ref': 'https://airflow.apache.org/docs/apache-airflow/stable/rest-api-ref.html#get--api-experimental-dags--DAG_ID--dag_runs',
                "client_id": client_id
            },
            {
                'description': 'Returns a JSON with a dag_runs public instance variables. The format for the <string:execution_date> is expected to be YYYY-mm-DDTHH:MM:SS, for example: 2016-11-16T11:34:15',
                'api_url': f'{airflow_uri}/dags/<string:dag_id>/dag_runs/<string:execution_date>',
                'http_method': 'GET',
                'api_ref': 'https://airflow.apache.org/docs/apache-airflow/stable/rest-api-ref.html#get--api-experimental-dags--string-dag_id--dag_runs--string-execution_date-',
                "client_id": client_id
            },
            {
                'description': 'To check REST API server correct work. Return status OK',
                'api_url': f'{airflow_uri}/test',
                'http_method': 'GET',
                'api_ref': 'https://airflow.apache.org/docs/apache-airflow/stable/rest-api-ref.html#get--api-experimental-test',
                "client_id": client_id
            },
            {
                'description': 'Returns info for a task',
                'api_url': f'{airflow_uri}/dags/<DAG_ID>/tasks/<TASK_ID>',
                'http_method': 'GET',
                'api_ref': 'https://airflow.apache.org/docs/apache-airflow/stable/rest-api-ref.html#get--api-experimental-dags--DAG_ID--tasks--TASK_ID-',
                "client_id": client_id
            },
            {
                'description': 'Returns a JSON with a task instance’s public instance variables. The format for the <string:execution_date> is expected to be YYYY-mm-DDTHH:MM:SS, for example: 2016-11-16T11:34:15',
                'api_url': f'{airflow_uri}/dags/<DAG_ID>/dag_runs/<string:execution_date>/tasks/<TASK_ID>',
                'http_method': 'GET',
                'api_ref': 'https://airflow.apache.org/docs/apache-airflow/stable/rest-api-ref.html#get--api-experimental-dags--DAG_ID--dag_runs--string-execution_date--tasks--TASK_ID-',
                "client_id": client_id
            },
            {
                'description': '<string:paused> must be a true to pause a DAG and false to unpause',
                'api_url': f'{airflow_uri}/dags/<DAG_ID>/paused/<string:paused>',
                'http_method': 'GET',
                'api_ref': 'https://airflow.apache.org/docs/apache-airflow/stable/rest-api-ref.html#get--api-experimental-dags--DAG_ID--paused--string-paused-',
                "client_id": client_id
            },
            {
                'description': 'Returns the latest DagRun for each DAG formatted for the UI',
                'api_url': f'{airflow_uri}/latest_runs',
                'http_method': 'GET',
                'api_ref': 'https://airflow.apache.org/docs/apache-airflow/stable/rest-api-ref.html#get--api-experimental-latest_runs',
                "client_id": client_id
            },
            {
                'description': 'Get all pools',
                'api_url': f'{airflow_uri}/pools',
                'http_method': 'GET',
                'api_ref': 'https://airflow.apache.org/docs/apache-airflow/stable/rest-api-ref.html#get--api-experimental-pools',
                "client_id": client_id
            },
            {
                'description': 'Get pool by a given name',
                'api_url': f'{airflow_uri}/pools/<string:name>',
                'http_method': 'GET',
                'api_ref': 'https://airflow.apache.org/docs/apache-airflow/stable/rest-api-ref.html#get--api-experimental-pools--string-name-',
                "client_id": client_id
            },
            {
                'description': 'Create a pool',
                'api_url': f'{airflow_uri}/pools',
                'http_method': 'POST',
                'api_ref': 'https://airflow.apache.org/docs/apache-airflow/stable/rest-api-ref.html#post--api-experimental-pools',
                "client_id": client_id
            },
            {
                'description': 'Delete a pool',
                'api_url': f'{airflow_uri}/pools/<string:name>',
                'http_method': 'DELETE',
                'api_ref': 'https://airflow.apache.org/docs/apache-airflow/stable/rest-api-ref.html#delete--api-experimental-pools--string-name-',
                "client_id": client_id
            }
        ]
    }
# [END get_next_actions_experimental_api]
