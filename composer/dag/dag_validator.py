#!/usr/bin/env python

"""dag_validator.py: Module that validates a Cloud Composer compatible dag based on a JSON DSL"""

__author__ = "Damian McDonald"
__credits__ = ["Damian McDonald"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Damian McDonald"
__status__ = "Development"

import logging
import os
import json
import importlib.util
from airflow import models
from composer.utils import log_service


class DagValidator:
    """Class used to validate and inspect an Airflow DAG"""

    # gets the logger for this module
    logger = log_service.get_module_logger(__name__)

    # [START DagValidator constructor]
    def __init__(self, dag_file):
        # set class logger
        self.dag_file = dag_file
    # [END DagValidator constructor]

    # [START load_dag_module]
    def load_dag_module(self):
        """
        Dynamically loads a concrete DAG file as a python module
        Returns:
            an instance of airflow.models.DAG
        """
        self.logger.log(logging.DEBUG, "Loading the dag module.")
        module_name = os.path.splitext(self.dag_file)[0]
        self.logger.log(logging.INFO, f"Loading dag module name: {module_name} from dag file: {self.dag_file}")
        spec = importlib.util.spec_from_file_location(module_name, self.dag_file)
        dag_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dag_module)
        return dag_module
    # [END load_dag_module]

    # [START assert_has_valid_dag]
    def assert_has_valid_dag(self):
        """
        Assert that a module contains a valid DAG.
        Returns:
            a boolean indicating if a dag is found. True == found, False == not found
        """
        self.logger.log(logging.DEBUG, "Asserting if the provided dag is valid.")
        dag_module = self.load_dag_module()

        no_dag_found = True

        for dag in vars(dag_module).values():
            if isinstance(dag, models.DAG):
                self.logger.log(logging.INFO, f"{dag_module} is a DAG instance")
                no_dag_found = False
                dag.test_cycle()  # Throws if a task cycle is found.

        if no_dag_found:
            raise AssertionError(f"DAG file {self.dag_file} does not contain a valid DAG")

        return no_dag_found
    # [END assert_has_valid_dag]

    # [START validate_dag]
    def validate_dag(self):
        """Verifies that a concrete DAG file is valid."""
        self.logger.log(logging.DEBUG, "Validating if the provided dag is valid.")
        self.assert_has_valid_dag()
    # [START validate_dag]

    # [START safe_serialize]
    def safe_serialize(self, obj):
        """
        Safely serialize a Python object to json - even when there are non-serializable attributes.
        Args:
            obj (Object): the object to be serialized
        Returns:
            a json string representing the serialized object
        """
        self.logger.log(logging.DEBUG, "Safely serializing the provided dag.")
        return json.dumps(obj, default=lambda o: f"<<non-serializable: {type(o).__qualname__}>>", indent=4)
    # [END safe_serialize]

    # [START inspect_dag]
    def inspect_dag(self):
        """
        Loads a DAG, validates the DAG and then dumps the DAG structure to a JSON string.
        Returns:
            an instance of the validated dag represented as a json string
        """
        self.logger.log(logging.DEBUG, "Inspecting the provided dag.")
        dag_module = self.load_dag_module()

        no_dag_found = True

        dag_as_str = ""

        for dag in vars(dag_module).values():
            if isinstance(dag, models.DAG):
                self.logger.log(logging.INFO, f"{dag_module} is a DAG instance")

                no_dag_found = False

                # put the dag details into a dictionary
                dag_dict = vars(dag)

                # iterate the task details and add to array
                tasks = []
                for task in dag.tasks:
                    tasks.append(vars(task))

                # inject the task details array into the dag details dictionary
                dag_dict['tasks_details'] = tasks

                # safely serialize the dict to json
                dag_as_str = self.safe_serialize(dag_dict)

        if no_dag_found:
            raise AssertionError(f"DAG file {self.dag_file} does not contain a valid DAG")

        return dag_as_str
    # [END inspect_dag]
