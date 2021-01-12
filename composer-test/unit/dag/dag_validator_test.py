import json
import os
import pytest
from pathlib import Path
from composer.dag import dag_generator
from composer.dag import dag_validator

DIR_DAGS_VALID = "payloads/valid"
DIR_DAGS_INVALID = "payloads/invalid"
DIR_DAGS_STATIC = "static"
EXT_PAYLOAD = ".json"
EXT_STATIC = ".py"


def get_test_files(dir, ext):
    return [f for f in os.listdir(os.path.join(os.path.dirname(Path(__file__)), dir)) if f.endswith(ext)]


def json_payload_to_dict(dir, json_file):
    with open(os.path.join(os.path.dirname(Path(__file__)), dir, json_file)) as f:
        payload = json.load(f)
    return payload


def test_validate_dag_from_payload():
    for test_dag in get_test_files(DIR_DAGS_VALID, EXT_PAYLOAD):
        dag_data = dag_generator.DagGenerator(json_payload_to_dict(DIR_DAGS_VALID, test_dag)).generate_dag()
        validator = dag_validator.DagValidator(dag_data['dag_file'])
        assert not validator.assert_has_valid_dag()


def test_validate_dag_from_static():
    for test_dag in get_test_files(DIR_DAGS_STATIC, EXT_STATIC):
        static_dag_file = os.path.join(os.path.dirname(Path(__file__)), DIR_DAGS_STATIC, test_dag)
        validator = dag_validator.DagValidator(static_dag_file)
        assert not validator.assert_has_valid_dag()


def test_inspect_dag_from_payload():
    for test_dag in get_test_files(DIR_DAGS_VALID, EXT_PAYLOAD):
        dag_data = dag_generator.DagGenerator(json_payload_to_dict(DIR_DAGS_VALID, test_dag)).generate_dag()
        validator = dag_validator.DagValidator(dag_data['dag_file'])
        assert json.loads(validator.inspect_dag()) is not None


def test_inspect_dag_from_static():
    for test_dag in get_test_files(DIR_DAGS_STATIC, EXT_STATIC):
        static_dag_file = os.path.join(os.path.dirname(Path(__file__)), DIR_DAGS_STATIC, test_dag)
        validator = dag_validator.DagValidator(static_dag_file)
        assert json.loads(validator.inspect_dag()) is not None


def test_validate_dag_from_payload_invalid():
    for test_dag in get_test_files(DIR_DAGS_INVALID, EXT_PAYLOAD):
        dag_data = dag_generator.DagGenerator(json_payload_to_dict(DIR_DAGS_INVALID, test_dag)).generate_dag()
        validator = dag_validator.DagValidator(dag_data['dag_file'])
        with pytest.raises(Exception):
            validator.assert_has_valid_dag()


test_validate_dag_from_payload()
test_validate_dag_from_static()
test_inspect_dag_from_payload()
test_inspect_dag_from_static()

test_validate_dag_from_payload_invalid()
