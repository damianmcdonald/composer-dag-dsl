#!/usr/bin/env python

"""api.py: Provides a public API with functionalities for validating, generating and deploying DAG files into
           a GCP Cloud Composer (Apache Airflow)."""

__author__ = "Damian McDonald"
__credits__ = ["Damian McDonald"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Damian McDonald"
__status__ = "Development"

import os
import logging
import traceback
from flask import Flask, jsonify, request
from flask_swagger_ui import get_swaggerui_blueprint
from composer.utils import log_service, auth_service
from composer.airflow import airflow_service
from composer.api import api_validator, api_service

# define the Flask web application
app = Flask(__name__, static_url_path='/static', static_folder='../static')
# indent the json for nicer, human readable output
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# gets the logger for this module
logger = log_service.get_module_logger(__name__)

# [START Swagger UI definitions]
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = "/static/api/swagger-api.yaml"
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL
)
app.register_blueprint(swaggerui_blueprint)
# Swagger docs are available at ${HOSTNAME}:${PORT}${SWAGGER_URL}
# e.g. localhost:5000/api/docs/
# [END Swagger UI definitions]

# Versioned, base path definition of API
API_BASE_PATH_V1 = '/api/v1'


# [START get_test]
@app.route(f'{API_BASE_PATH_V1}/test', methods=['GET'])
def get_test():
    """Test method to verify that the API is functioning correctly"""
    logger.log(logging.INFO, f"Entered get_test -- {API_BASE_PATH_V1}/test api GET method")
    return jsonify(
        env_vars=dict(os.environ)
    )
# [END get_test]


# [START get_composer_config]
@app.route(f'{API_BASE_PATH_V1}/composer/config', methods=['GET'])
def get_composer_config():
    """Gets the configuration information of the Cloud Composer environment"""
    logger.log(logging.INFO, f"Entered get_composer_config -- {API_BASE_PATH_V1}/composer/config api GET method")
    req_data = request.get_json()
    if req_data:
        logger.log(logging.DEBUG, f"Request contains a json payload, validating: {req_data}")
        api_validator.validate_project_json(req_data)
        project_id, location, composer_environment = api_service.get_gcp_composer_details(req_data)
    else:
        logger.log(logging.DEBUG, f"Request does not contain a json payload, validating implicitly")
        project_id, location, composer_environment = api_service.get_gcp_composer_details(None)

    authenticated_session = auth_service.get_authenticated_session()
    airflow_config = airflow_service.AirflowService(
        authenticated_session,
        project_id,
        location,
        composer_environment
    ).get_airflow_config()

    next_actions = {
        'list': f'{API_BASE_PATH_V1}/dag/list',
        'validate': f'{API_BASE_PATH_V1}/dag/validate',
        'deploy': f'{API_BASE_PATH_V1}/dag/deploy'
    }

    return jsonify(
        airflow_config=airflow_config,
        next_actions=next_actions
    )
# [END get_composer_config]


# [START get_composer_experimental_apì]
@app.route(f'{API_BASE_PATH_V1}/composer/api', methods=['GET'])
def get_composer_experimental_apì():
    """Gets the configuration information of the Cloud Composer experimental API"""
    logger.log(logging.INFO, f"Entered get_composer_experimental_apì -- {API_BASE_PATH_V1}/composer/api api GET method")
    req_data = request.get_json()
    if req_data:
        logger.log(logging.DEBUG, f"Request contains a json payload, validating: {req_data}")
        api_validator.validate_project_json(req_data)
        project_id, location, composer_environment = api_service.get_gcp_composer_details(req_data)
    else:
        logger.log(logging.DEBUG, f"Request does not contain a json payload, validating implicitly")
        project_id, location, composer_environment = api_service.get_gcp_composer_details(None)

    authenticated_session = auth_service.get_authenticated_session()
    airflow_uri, client_id = airflow_service.AirflowService(
        authenticated_session,
        project_id,
        location,
        composer_environment
    ).get_airflow_experimental_api()

    return jsonify(
        airflow_uri=airflow_uri,
        client_id=client_id,
        next_actions=api_service.get_next_actions_experimental_api(airflow_uri, client_id)
    )
# [END get_composer_experimental_apì]


# [START list_dags]
@app.route(f'{API_BASE_PATH_V1}/dag/list', methods=['GET'])
def list_dags():
    """Lists the dags stored in the Cloud Composer GCS bucket"""
    logger.log(logging.INFO, f"Entered list_dags -- {API_BASE_PATH_V1}/dag/list api GET method")
    req_data = request.get_json()
    if req_data:
        logger.log(logging.DEBUG, f"Request contains a json payload, validating: {req_data}")
        api_validator.validate_project_json(req_data)
        project_id, location, composer_environment = api_service.get_gcp_composer_details(req_data)
        bucket_name = api_service.get_dag_bucket(project_id, location, composer_environment)
    else:
        logger.log(logging.DEBUG, f"Request does not contain a json payload, validating implicitly")
        project_id, location, composer_environment = api_service.get_gcp_composer_details(None)
        bucket_name = api_service.get_dag_bucket(project_id, location, composer_environment)

    dag_list = api_service.list_dags(project_id, bucket_name)

    next_actions = {
        'validate': f'{API_BASE_PATH_V1}/dag/validate',
        'deploy': f'{API_BASE_PATH_V1}/dag/deploy'
    }

    return jsonify(
        dag_list=dag_list,
        next_actions=next_actions
    )
# [END list_dags]


# [START validate_dag]
@app.route(f'{API_BASE_PATH_V1}/dag/validate', methods=['POST'])
def validate_dag():
    """Validates a dag to ensure that it is error free and compatible with Cloud Composer"""
    logger.log(logging.INFO, f"Entered validate_dag -- {API_BASE_PATH_V1}/dag/validate api POST method")
    req_data = request.get_json()
    if not req_data:
        return {'error': "Empty JSON payload"}, 500
    try:
        api_validator.validate_payload(req_data)
        if 'project_id' in req_data:
            project_id, location, composer_environment = api_service.get_gcp_composer_details(req_data)
        else:
            project_id, location, composer_environment = api_service.get_gcp_composer_details(None)

        next_actions = {
            'deploy': f'{API_BASE_PATH_V1}/dag/deploy'
        }

        if req_data['mode'] == 'GCS':
            deploy_file = api_service.gcs_download_file(project_id, req_data['bucket_name'], req_data['file_path'])
            validation_json = api_service.validate_dag('GCS', deploy_file)
            validation_json['next_actions'] = next_actions
            return jsonify(validation_json)

        if req_data['mode'] == 'GIT':
            deploy_file = api_service.git_download_file(
                req_data['git_url'],
                req_data['repo_name'],
                req_data['file_path']
            )
            validation_json = api_service.validate_dag('GIT', deploy_file)
            validation_json['next_actions'] = next_actions
            return jsonify(validation_json)

        if req_data['mode'] == 'INLINE':
            validation_json = api_service.validate_dag('INLINE', req_data)
            validation_json['next_actions'] = next_actions
            return jsonify(validation_json)

    except:
        return {'error': traceback.print_exc()}, 500
# [END validate_dag]


# [START deploy_dag]
@app.route(f'{API_BASE_PATH_V1}/dag/deploy', methods=['POST'])
def deploy_dag():
    """Deploys a dag to a Cloud Composer environment"""
    logger.log(logging.INFO, f"Entered deploy_dag -- {API_BASE_PATH_V1}/dag/deploy api POST method")
    req_data = request.get_json()
    if not req_data:
        return {'error': "Empty JSON payload"}, 500
    try:
        api_validator.validate_payload(req_data)
        if 'project_id' in req_data:
            project_id, location, composer_environment = api_service.get_gcp_composer_details(req_data)
        else:
            project_id, location, composer_environment = api_service.get_gcp_composer_details(None)

        airflow_dag_bucket_name = api_service.get_dag_bucket(project_id, location, composer_environment)
        dag_name = req_data['dag_name']

        next_actions = {
            'trigger': f'{API_BASE_PATH_V1}/dag/trigger/{dag_name}'
        }

        if req_data['mode'] == 'GCS':
            deploy_file = api_service.gcs_download_file(project_id, req_data['bucket_name'], req_data['file_path'])
            gcs_dag_path = api_service.deploy_dag(project_id, 'GCS', airflow_dag_bucket_name, dag_file=deploy_file)
            return jsonify(
                dag_name=dag_name,
                dag_gcs_path=gcs_dag_path,
                next_actions=next_actions
            )

        if req_data['mode'] == 'GIT':
            deploy_file = api_service.git_download_file(
                req_data['git_url'],
                req_data['repo_name'],
                req_data['file_path']
            )
            git_dag_path = api_service.deploy_dag(project_id, 'GIT', airflow_dag_bucket_name, dag_file=deploy_file)
            return jsonify(
                dag_name=dag_name,
                dag_gcs_path=git_dag_path,
                next_actions=next_actions
            )

        if req_data['mode'] == 'INLINE':
            gcs_dag_path = api_service.deploy_dag(project_id, 'INLINE', airflow_dag_bucket_name, dag_data=req_data)
            return jsonify(
                dag_name=dag_name,
                dag_gcs_path=gcs_dag_path,
                next_actions=next_actions
            )
    except:
        return {'error': traceback.print_exc()}, 500
# [END deploy_dag]


# [START trigger_dag]
@app.route(f'{API_BASE_PATH_V1}/dag/trigger/<dag_name>', methods=['PUT'])
def trigger_dag(dag_name):
    """Triggers a specific, existing dag within a Cloud Composer environment"""
    logger.log(logging.INFO, f"Entered trigger_dag -- {API_BASE_PATH_V1}/dag/trigger/{dag_name} api PUT method")
    req_data = request.get_json()
    if req_data:
        if 'conf' not in req_data or len(req_data['conf']) == 0:
            return {'error': "JSON payload provided but conf element is missing or empty"}, 500
        if 'project_id' in req_data:
            api_validator.validate_project_json(req_data)
            project_id, location, composer_environment = api_service.get_gcp_composer_details(req_data)
    else:
        project_id, location, composer_environment = api_service.get_gcp_composer_details(None)
    try:
        res = api_service.trigger_dag(project_id, location, composer_environment, dag_name)
    except:
        return {'error': traceback.print_exc()}, 500

    authenticated_session = auth_service.get_authenticated_session()
    airflow_uri, client_id = airflow_service.AirflowService(
        authenticated_session,
        project_id,
        location,
        composer_environment
    ).get_airflow_experimental_api()

    return jsonify(
        api_response=res,
        next_actions=api_service.get_next_actions_experimental_api(airflow_uri, client_id)
    )
# [END trigger_dag]


# [Flask application entrypoint]
if __name__ == '__main__':
    app.run(debug=True)
