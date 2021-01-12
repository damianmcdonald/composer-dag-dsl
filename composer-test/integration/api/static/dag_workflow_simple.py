import datetime
import airflow
from airflow.operators import bash_operator
from airflow.operators import python_operator
from airflow.contrib.operators import kubernetes_pod_operator


YESTERDAY = datetime.datetime.now() - datetime.timedelta(days=1)

default_args = {
    'start_date': YESTERDAY
}

dag = airflow.DAG(
    'simple_workflow_dag',
    default_args=default_args,
    schedule_interval=None
)

bash_operator_task = bash_operator.BashOperator(
    task_id='bash_operator_example_task',
    bash_command='echo "Hello from Airflow Bash Operator"',
    dag=dag
)


def python_operator_func():
    print("Hello from Airflow Python Operator")


python_operator_task = python_operator.PythonOperator(
    task_id='python_operator_example_task',
    python_callable=python_operator_func,
    dag=dag
)


kubernetes_pod_operator_task = kubernetes_pod_operator.KubernetesPodOperator(
    task_id='k8s_pod_operator_example_task',
    name='k8s_pod_example',
    namespace='default',
    image='bash',
    cmds=['echo'],
    arguments=['"Hello from Airflow Kubernetes Pod Operator"'],
    dag=dag
)
