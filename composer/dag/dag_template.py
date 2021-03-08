#!/usr/bin/env python

"""dag_template.py: Template used to generate a Cloud Composer compatible dag based on a JSON DSL"""

__author__ = "Damian McDonald"
__credits__ = ["Damian McDonald"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Damian McDonald"
__status__ = "Development"

import json
from pprint import pprint
import os
import ntpath
import datetime
from pathlib import Path
import airflow
from airflow.operators import bash_operator
from airflow.operators import python_operator
from airflow.contrib.kubernetes import secret
from airflow.contrib.operators import kubernetes_pod_operator
"""
NOTE: the above import statements are used dynamically within the template. Even though an IDE may indicate
they are not used, please only remove the following imports if you are absolutely sure they are not required.
"""

# [START insertion of dynamic code]
# >>>INSERTION_MARKER<<<

# [END insertion of dynamic code]


# [START find_key_in_dict]
def find_key_in_dict(key, dictionary):
    """
    Finds a key in a Python dictionary.
    Args:
        key (string): the key to find in the dictionary
        dictionary (string): the dictionary in which to search for the key

    Returns a generator which should be cast as a list
        * The list will be empty if the key is NOT found
        * The list will contain the key value if it is found

    Usage: list(find_key_in_dict('my_key', my_dict))
    """
    for k, v in dictionary.items():
        if k == key:
            yield v
        elif isinstance(v, dict):
            for result in find_key_in_dict(key, v):
                yield result
        elif isinstance(v, list):
            for d in v:
                if isinstance(d, dict):
                    for result in find_key_in_dict(key, d):
                        yield result
# [END find_key_in_dict]


# [START dynamic function declarations]
dynamic_functions = {}


def get_dynamic_function(key_name, func_def, func_name, func_dict):
    """
    Defines a dynamic function.
    Args:
        key_name (string): the json element name of the function block
        func_def (string): the json element name of the function definition
        func_name (string): the json element name of the function name
        func_dict (string): the global dictionary in which to store the dynamic function
    """
    if not list(find_key_in_dict(func_def, func_dict)):
        raise ValueError(
            f"{key_name} dynamic function requested but '{func_def}' was not found."
        )
    if not list(find_key_in_dict(func_name, func_dict)):
        raise ValueError(
            f"{key_name} dynamic function requested but '{func_name}' was not found."
        )

    exec("\n".join(func_dict[func_def]), dynamic_functions)
    return dynamic_functions[func_dict[func_name]]()
# [END dynamic function declarations]


# [START build_kubernetes_pod_operator]
def build_kubernetes_pod_operator(operator_ref, dag_ref):
    """
    Builds a DAG operator of type: KubernetesPodOperator.
    Args:
        operator_ref (string): the definition of the operator
        dag_ref (string): the reference to the dag to associate this operator
    """
    op = kubernetes_pod_operator.KubernetesPodOperator(
        task_id=operator_ref['task_id'],
        name=operator_ref['name'],
        image=operator_ref['image'],
        namespace=operator_ref['namespace'] if 'namespace' in operator_ref else 'default',
        dag=dag_ref
    )

    # populate non-default operator values
    if 'cmds' in operator_ref:
        op.cmds = operator_ref['cmds']

    if 'arguments' in operator_ref:
        op.arguments = operator_ref['arguments']

    if 'env_vars' in operator_ref:
        op.env_vars = operator_ref['env_vars']

    if 'labels' in operator_ref:
        op.env_vars = operator_ref['labels']

    if 'startup_timeout_seconds' in operator_ref:
        op.startup_timeout_seconds = operator_ref['startup_timeout_seconds']

    if 'ports' in operator_ref:
        op.ports = operator_ref['ports']

    if 'params' in operator_ref:
        op.params = operator_ref['params']

    if 'node_selectors' in operator_ref:
        op.node_selectors = operator_ref['node_selectors']

    if 'resources' in operator_ref:
        op.resources = operator_ref['resources']

    if 'config_file' in operator_ref:
        op.config_file = operator_ref['config_file']

    if 'annotations' in operator_ref:
        op.annotations = operator_ref['annotations']

    if 'volumes' in operator_ref:
        op.volumes = operator_ref['volumes']

    if 'volume_mounts' in operator_ref:
        op.volumes = operator_ref['volume_mounts']

    if 'affinity' in operator_ref:
        op.affinity = operator_ref['affinity']

    if 'configmaps' in operator_ref:
        op.configmaps = operator_ref['configmaps']

    # define pod secrets
    pod_secrets = []
    if 'pod_secret_refs' in operator_ref:
        for pod_secret in operator_ref['pod_secret_refs']:
            if not list(find_key_in_dict('kubernetes_secrets', payload)):
                raise ValueError(
                    f"Pod {operator_ref['name']} declares 'pod_secret_refs' but 'kubernetes_secrets' has not been defined."
                )

            secret_entry_ref = payload['kubernetes_secrets'][pod_secret]
            secret_entry = secret.Secret(
                # Deploy type: 'env' for environment  variable or 'volume'
                deploy_type=secret_entry_ref['deploy_type'],
                # The name of the environment variable or the path of the volume
                deploy_target=secret_entry_ref['deploy_target'],
                # Name of the Kubernetes Secret
                secret=secret_entry_ref['secret'],
                # Key of a secret stored in this Secret object or key in the form of service account file name
                key=secret_entry_ref['key']
            )
            pod_secrets.append(secret_entry)

        op.secrets = pod_secrets

        if 'image_pull_policy' in operator_ref:
            op.image_pull_policy = operator_ref['image_pull_policy']

        # define pull secrets
        image_pull_secrets = []
        if 'image_pull_secret_refs' in operator_ref:
            for image_pull_secret in operator_ref['image_pull_secret_refs']:
                if not list(find_key_in_dict('kubernetes_secrets', payload)):
                    raise ValueError(
                        f"Pod {operator_ref['name']} declares 'image_pull_secret_refs' but 'kubernetes_secrets' has not been defined."
                    )

                secret_entry_ref = payload['kubernetes_secrets'][image_pull_secret]
                secret_entry = secret.Secret(
                    # Deploy type: 'env' for environment  variable or 'volume'
                    deploy_type=secret_entry_ref['deploy_type'],
                    # The name of the environment variable or the path of the volume
                    deploy_target=secret_entry_ref['deploy_target'],
                    # Name of the Kubernetes Secret
                    secret=secret_entry_ref['secret'],
                    # Key of a secret stored in this Secret object or key in the form of service account file name
                    key=secret_entry_ref['key']
                )
                image_pull_secrets.append(secret_entry)

            op.image_pull_secrets = image_pull_secrets

    return operator
# [END build_kubernetes_pod_operator]


# [START build_python_operator]
def build_python_operator(operator_ref, dag_ref):
    """
    Builds a DAG operator of type: PythonOperator.
    Args:
        operator_ref (string): the definition of the operator
        dag_ref (string): the reference to the dag to associate this operator
    """
    dynamic_func = {}
    exec("\n".join(operator_ref['function_def']), dynamic_func)

    op = python_operator.PythonOperator(
        task_id=operator_ref['task_id'],
        python_callable=dynamic_func[operator_ref['function_name']],
        dag=dag_ref
    )

    return op
# [END build_python_operator]


# [START build_bash_operator]
def build_bash_operator(operator_ref, dag_ref):
    """
    Builds a DAG operator of type: BashOperator.
    Args:
        operator_ref (string): the definition of the operator
        dag_ref (string): the reference to the dag to associate this operator
    """
    op = bash_operator.BashOperator(
        task_id=operator_ref['task_id'],
        bash_command=";".join(operator_ref['command']),
        dag=dag_ref
    )

    return op
# [END build_bash_operator]

# [START build_gke_start_pod_operator]
def build_gke_start_pod_operator(operator_ref, dag_ref):
    """
    Builds a DAG operator of type: GKEStartPodOperator.
    Args:
        operator_ref (string): the definition of the operator
        dag_ref (string): the reference to the dag to associate this operator
    """
    op = GKEStartPodOperator(
        task_id=operator_ref['task_id'],
        name=operator_ref['name'],
        image=operator_ref['image'],
        cluster_name=operator_ref['cluster_name'],
        project_id=operator_ref['project_id'],
        location=operator_ref['location'],
        namespace=operator_ref['namespace'] if 'namespace' in operator_ref else 'default',
        dag=dag_ref
    )

    # populate non-default operator values
    if 'cmds' in operator_ref:
        op.cmds = operator_ref['cmds']

    if 'arguments' in operator_ref:
        op.arguments = operator_ref['arguments']

    if 'env_vars' in operator_ref:
        op.env_vars = operator_ref['env_vars']

    if 'labels' in operator_ref:
        op.env_vars = operator_ref['labels']

    if 'startup_timeout_seconds' in operator_ref:
        op.startup_timeout_seconds = operator_ref['startup_timeout_seconds']

    if 'ports' in operator_ref:
        op.ports = operator_ref['ports']

    if 'params' in operator_ref:
        op.params = operator_ref['params']

    if 'node_selectors' in operator_ref:
        op.node_selectors = operator_ref['node_selectors']

    if 'resources' in operator_ref:
        op.resources = operator_ref['resources']

    if 'annotations' in operator_ref:
        op.annotations = operator_ref['annotations']

    if 'volumes' in operator_ref:
        op.volumes = operator_ref['volumes']

    if 'volume_mounts' in operator_ref:
        op.volumes = operator_ref['volume_mounts']

    if 'affinity' in operator_ref:
        op.affinity = operator_ref['affinity']

    if 'configmaps' in operator_ref:
        op.configmaps = operator_ref['configmaps']

    # define pod secrets
    pod_secrets = []
    if 'pod_secret_refs' in operator_ref:
        for pod_secret in operator_ref['pod_secret_refs']:
            if not list(find_key_in_dict('kubernetes_secrets', payload)):
                raise ValueError(
                    f"Pod {operator_ref['name']} declares 'pod_secret_refs' but 'kubernetes_secrets' has not been defined."
                )

            secret_entry_ref = payload['kubernetes_secrets'][pod_secret]
            secret_entry = secret.Secret(
                # Deploy type: 'env' for environment  variable or 'volume'
                deploy_type=secret_entry_ref['deploy_type'],
                # The name of the environment variable or the path of the volume
                deploy_target=secret_entry_ref['deploy_target'],
                # Name of the Kubernetes Secret
                secret=secret_entry_ref['secret'],
                # Key of a secret stored in this Secret object or key in the form of service account file name
                key=secret_entry_ref['key']
            )
            pod_secrets.append(secret_entry)

        op.secrets = pod_secrets

        if 'image_pull_policy' in operator_ref:
            op.image_pull_policy = operator_ref['image_pull_policy']

        # define pull secrets
        image_pull_secrets = []
        if 'image_pull_secret_refs' in operator_ref:
            for image_pull_secret in operator_ref['image_pull_secret_refs']:
                if not list(find_key_in_dict('kubernetes_secrets', payload)):
                    raise ValueError(
                        f"Pod {operator_ref['name']} declares 'image_pull_secret_refs' but 'kubernetes_secrets' has not been defined."
                    )

                secret_entry_ref = payload['kubernetes_secrets'][image_pull_secret]
                secret_entry = secret.Secret(
                    # Deploy type: 'env' for environment  variable or 'volume'
                    deploy_type=secret_entry_ref['deploy_type'],
                    # The name of the environment variable or the path of the volume
                    deploy_target=secret_entry_ref['deploy_target'],
                    # Name of the Kubernetes Secret
                    secret=secret_entry_ref['secret'],
                    # Key of a secret stored in this Secret object or key in the form of service account file name
                    key=secret_entry_ref['key']
                )
                image_pull_secrets.append(secret_entry)

            op.image_pull_secrets = image_pull_secrets

    return operator
# [END build_gke_start_pod_operator]

# [START default_args definitions]
default_args = {}

# add default arguments if they have been specified
if list(find_key_in_dict('default_args', payload)):
    for key in payload['default_args']:
        default_args[key] = payload['default_args'][key]

# add the retry_delay if it has been specified
if list(find_key_in_dict('retry_delay', payload)):
    default_args['retry_delay'] = get_dynamic_function(
        'retry_delay',
        'retry_delay_def',
        'retry_delay_name',
        payload['dynamic_functions']['retry_delay']
    )
# [END default_args definitions]


# [START DAG definition]
dag = airflow.DAG(
    payload['dag_name'],
    default_args=default_args
)

# add the start_date
if not list(find_key_in_dict('start_date', payload)):
    dag.start_date = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(days=1)
else:
    dag.start_date = get_dynamic_function(
        'start_date',
        'start_date_def',
        'start_date_name',
        payload['dynamic_functions']['start_date']
    )


# add the schedule_interval
if list(find_key_in_dict('schedule_interval', payload)):
    dag.schedule_interval = get_dynamic_function(
        'schedule_interval',
        'schedule_interval_def',
        'schedule_interval_name',
        payload['dynamic_functions']['schedule_interval']
    )

# add the dag run timeout
if list(find_key_in_dict('dagrun_timeout', payload)):
    dag.dagrun_timeout = get_dynamic_function(
        'dagrun_timeout',
        'dagrun_timeout_def',
        'dagrun_timeout_name',
        payload['dynamic_functions']['dagrun_timeout']
    )

if 'dag_tags' in payload:
    dag.tags = payload['dag_tags']

if 'dag_params' in payload:
    dag.params = payload['dag_params']

if 'dag_doc_md' in payload:
    dag.doc_md = "\n".join(payload['dag_doc_md'])
# [END DAG definition]


# [START add operators to DAG]
if (
        not list(find_key_in_dict('bash_operators', payload))
        and not list(find_key_in_dict('python_operators', payload))
        and not list(find_key_in_dict('kubernetes_pod_operators', payload))
        and not list(find_key_in_dict('gke_start_pod_operators', payload))
):
    raise ValueError(
        "A DAG definition must contain at least one of; bash_operators, python_operators or kubernetes_pod_operators."
    )

if (
        ('bash_operators' in payload and not len(payload['bash_operators']) > 0)
        or ('python_operators' in payload and not len(payload['python_operators']) > 0)
        or ('kubernetes_pod_operators' in payload and not len(payload['kubernetes_pod_operators']) > 0)
        or ('gke_start_pod_operators' in payload and not len(payload['gke_start_pod_operators']) > 0)
):
    raise ValueError(
        "A DAG definition must contain at least one element in; bash_operators, python_operators or kubernetes_pod_operators."
    )

if list(find_key_in_dict('bash_operators', payload)):
    bash_operators = payload['bash_operators']
    for operator in bash_operators:
        build_bash_operator(operator, dag)

if list(find_key_in_dict('python_operators', payload)):
    python_operators = payload['python_operators']
    for operator in python_operators:
        build_python_operator(operator, dag)

if list(find_key_in_dict('kubernetes_pod_operators', payload)):
    kubernetes_pod_operators = payload['kubernetes_pod_operators']
    for operator in kubernetes_pod_operators:
        build_kubernetes_pod_operator(operator, dag)

if list(find_key_in_dict('gke_start_pod_operators', payload)):
    gke_start_pod_operators = payload['gke_start_pod_operators']
    for operator in gke_start_pod_operators:
        build_gke_start_pod_operator(operator, dag)
# [END add operators to DAG]


# [START validate_execution_sequence]
def validate_execution_sequence(task_list):
    """
    Validates a DAG execution sequence.
    Args:
        task_list (string): the list of tasks to be validated within a dag
    """
    for task in task_list:
        if not dag.has_task(task):
            raise ValueError(
                f"Task {task} is specified as a task in the 'execution_sequence' "
                "but it has not been defined as a DAG task"
            )
# [END validate_execution_sequence]


# [START define the sequence of task execution]
if list(find_key_in_dict('execution_sequence', payload)):
    execution_sequence_ref = payload['execution_sequence']

    # validate that the tasks exist in the dag
    validate_execution_sequence(execution_sequence_ref)

    # define the sequence using the >> operator
    execution_sequence_str = ' >> '.join([f"dag.get_task('{elem}')" for elem in execution_sequence_ref])
    execution_sequence_def = ["def execution_sequence_def(dag):", f"    {execution_sequence_str}"]

    # create and execute sequence dynamic function
    exec("\n".join(execution_sequence_def), dynamic_functions)
    dynamic_functions["execution_sequence_def"](dag)
# [END define the sequence of task execution]
