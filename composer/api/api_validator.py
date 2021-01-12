#!/usr/bin/env python

"""api_validator.py: Module that provides validation functions to ensure that the incoming JSON payloads
                     contain valid and mandatory details"""

__author__ = "Damian McDonald"
__credits__ = ["Damian McDonald"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Damian McDonald"
__status__ = "Development"

import logging
from composer.utils import log_service

# gets the logger for this module
logger = log_service.get_module_logger(__name__)


# [START validate_project_json]
def validate_project_json(project_json):
    """
    Validates the JSON payload to confirm that it contains the mandatory details.
    Args:
        project_json (string): JSON payload which includes a project_id, location and composer_environment elements
    Returns:
        a boolean indicating if the provided payload is valid otherwise an exception
    """
    logger.log(logging.DEBUG, "Validating the payload to determine correct GCP project data.")
    if "project_id" not in project_json:
        raise ValueError(f"Json payload provided but it does not contain 'project_id': {project_json}")
    if "location" not in project_json:
        raise ValueError(f"Json payload provided but it does not contain 'location': {project_json}")
    if "composer_environment" not in project_json:
        raise ValueError(f"Json payload provided but it does not contain 'composer_environment': {project_json}")
    return True
# [END validate_project_json]


# [START validate_payload]
def validate_payload(payload_json):
    """
    Validates the JSON payload to confirm that it contains the mandatory details.
    Args:
        payload_json (string): JSON payload which contains the details of a Cloud Composer compatible dag
    Returns:
        a boolean indicating if the provided payload is valid otherwise an exception
    """
    logger.log(logging.DEBUG, "Validating the payload to determine correct JSON data.")
    if "dag_name" not in payload_json:
        raise ValueError(f"Json payload does not contain 'dag_name': {payload_json}")
    if "mode" not in payload_json:
        raise ValueError(f"Json payload does not contain 'mode': {payload_json}")
    if payload_json['mode'] not in ["INLINE", "GCS", "GIT"]:
        raise ValueError(f"Json payload does not contain a valid mode, INLINE, GCS or GIT: {payload_json}")
    if payload_json['mode'] == "INLINE":
        __validate_dsl_json(payload_json)
    if payload_json['mode'] == "GCS":
        if 'bucket_name' not in payload_json:
            raise ValueError(f"'GCS mode specified but no bucket_name provided': {payload_json}")
        if 'file_path' not in payload_json:
            raise ValueError(f"'GCS mode specified but no dag_file provided': {payload_json}")
    if payload_json['mode'] == "GIT":
        if 'git_url' not in payload_json:
            raise ValueError(f"'GIT mode specified but no git_url provided': {payload_json}")
        if 'repo_name' not in payload_json:
            raise ValueError(f"'GIT mode specified but no repo_name provided': {payload_json}")
        if 'file_path' not in payload_json:
            raise ValueError(f"'GIT mode specified but no file_path provided': {payload_json}")
    return True
# [END validate_payload]


# [START __validate_dsl_json]
def __validate_dsl_json(dsl_json):
    """
    Validates the JSON DSL payload to confirm that it contains the mandatory details.
    Args:
        dsl_json (string): JSON DSL payload which describes a Cloud Composer compatible dag
    Returns:
        a boolean indicating if the provided payload is valid otherwise an exception
    """
    logger.log(logging.DEBUG, "Validating the payload to determine correct JSON DSL dag data.")
    if "dag_name" not in dsl_json:
        raise ValueError(f"Json payload does not contain 'dag_name': {dsl_json}")
    if "kubernetes_pod_operators" in dsl_json:
        if len(dsl_json['kubernetes_pod_operators']) == 0:
            raise ValueError(f"'kubernetes_pod_operators' defined but it contains no elements")
        for operator in dsl_json['kubernetes_pod_operators']:
            if 'task_id' not in operator:
                raise ValueError(f"'kubernetes_pod_operator' defined but it does not contains a 'task_id': {operator}")
            if 'name' not in operator:
                raise ValueError(f"'kubernetes_pod_operator' defined but it does not contains a 'name': {operator}")
            if 'image' not in operator:
                raise ValueError(f"'kubernetes_pod_operator' defined but it does not contains a 'image': {operator}")
    if "bash_operators" in dsl_json:
        if len(dsl_json['bash_operators']) == 0:
            raise ValueError(f"'bash_operators' defined but it contains no elements")
        for operator in dsl_json['bash_operators']:
            if 'task_id' not in operator:
                raise ValueError(f"'bash_operator' defined but it does not contains a 'task_id': {operator}")
            if 'command' not in operator:
                raise ValueError(f"'bash_operator' defined but it does not contains a 'command': {operator}")
            if len(operator['command']) == 0:
                raise ValueError(f"'bash_operator.command' defined but it does not contains any commands: {operator}")
    if "python_operators" in dsl_json:
        if len(dsl_json['python_operators']) == 0:
            raise ValueError(f"'python_operators' defined but it contains no elements")
        for operator in dsl_json['python_operators']:
            if 'task_id' not in operator:
                raise ValueError(f"'python_operators' defined but it does not contains a 'task_id': {operator}")
            if 'function_name' not in operator:
                raise ValueError(f"'python_operators' defined but it does not contains a 'function_name': {operator}")
            if 'function_def' not in operator:
                raise ValueError(f"'python_operators' defined but it does not contains a 'function_def': {operator}")
            if len(operator['function_def']) == 0:
                raise ValueError(f"'python_operator.function_def' defined but it does not contains any code: {operator}")
    return True
# [END __validate_dsl_json]
