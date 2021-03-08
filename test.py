import os

from airflow import models
from airflow.providers.google.cloud.operators.kubernetes_engine import GKEStartPodOperator
from airflow.utils.dates import days_ago

with models.DAG(
    "testgithubbruno",
    schedule_interval=None,  # Override to match your needs
    start_date=days_ago(1),
    tags=['example'],
) as dag:

    pod_task = GKEStartPodOperator(
        task_id="pod_task",
        project_id="telefonica-digital-cloud",
        location="europe-west2-b",
        cluster_name="europe-west2-composer-c96de2c4-gke",
        namespace="default",
        image="us-docker.pkg.dev/cloudrun/container/hello",
        name="test-pod232",
    )