import os
import json
from pathlib import Path
from composer.dag import dag_generator


DIR_DAGS_VALID = "payloads/valid"
PAYLOAD_EXT = ".json"


def get_test_files(dir, ext):
    return [f for f in os.listdir(os.path.join(os.path.dirname(Path(__file__)), dir)) if f.endswith(ext)]


def test_generate_dag_valid():
    def json_payload_to_dict(json_file):
        with open(os.path.join(os.path.dirname(Path(__file__)), DIR_DAGS_VALID, json_file)) as f:
            payload = json.load(f)
        return payload

    for test_dag in get_test_files(DIR_DAGS_VALID, PAYLOAD_EXT):
        generator = dag_generator.DagGenerator(json_payload_to_dict(test_dag))
        dag_data = generator.generate_dag()
        assert os.path.exists(dag_data['dag_file'])
        assert os.path.exists(dag_data['json_file'])


test_generate_dag_valid()
