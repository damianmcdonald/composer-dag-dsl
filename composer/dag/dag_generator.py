#!/usr/bin/env python

"""dag_generator.py: Module that generates Cloud Composer compatible dag files from on a JSON DSL"""

__author__ = "Damian McDonald"
__credits__ = ["Damian McDonald"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Damian McDonald"
__status__ = "Development"

import os
import ntpath
import shutil
import re
import json
import tempfile
import logging
from pathlib import Path
from composer.utils import log_service


class DagGenerator:
    """Class used to generate an Airflow DAG based on a JSON DSL definition"""

    # [START global variable definitions]
    INSERTION_MARKER = "# >>>INSERTION_MARKER<<<"
    DAG_TEMPLATE = "dag_template.py"
    EXTENSION_PYTHON = ".py"
    EXTENSION_JSON = ".json"
    # [END global variable definitions]

    # gets the logger for this module
    logger = log_service.get_module_logger(__name__)

    # [START DagGenerator constructor]
    def __init__(self, payload):
        # set class logger
        # sanitize the dag_name - replace whitespace with underscores and convert to lowercase
        self.payload = payload
        self.dag_name = re.sub(r'\s+', '_', payload['dag_name']).lower()
        self.temp_dir = tempfile.gettempdir()
        # define the path for the dag file and its associated json data
        # these are the paths where the concrete dag will be created
        self.dag_file = os.path.join(self.temp_dir, f"{self.dag_name}{self.EXTENSION_PYTHON}")
        self.json_file = os.path.join(self.temp_dir, f"{self.dag_name}{self.EXTENSION_JSON}")
    # [END DagGenerator constructor]

    # [START remove_previous_versions]
    def remove_previous_versions(self):
        """Removes any existing dag or json file that uses the provided dag name"""
        self.logger.log(logging.DEBUG, "Removes any previous version of the dag.")
        if os.path.exists(self.dag_file):
            os.remove(self.dag_file)
            self.logger.log(logging.INFO, f"Removed previous dag version: {self.dag_file}")
        else:
            self.logger.log(logging.INFO, f"No previous dag version: {self.dag_file}")

        if os.path.exists(self.json_file):
            os.remove(self.json_file)
            self.logger.log(logging.INFO, f"Removed previous json version: {self.json_file}")
        else:
            self.logger.log(logging.INFO, f"No previous json version: {self.json_file}")
    # [END remove_previous_versions]

    # [START copy_dag_template_to_file]
    def copy_dag_template_to_file(self):
        """Copies the dag template to a concrete dag file"""
        self.logger.log(logging.DEBUG, "Copying the dag template to a file.")
        template_src = os.path.join(os.path.dirname(Path(__file__)), self.DAG_TEMPLATE)
        self.logger.log(logging.INFO, f"Copying template: {template_src} to {self.dag_file}")
        shutil.copy(template_src, self.dag_file)
    # [END copy_dag_template_to_file]

    # [START write_payload_to_file]
    def write_payload_to_file(self):
        """Writes the provided, in-memory json payload to a concrete json file"""
        self.logger.log(logging.INFO, f"Writing payload to: {self.json_file}")
        with open(self.json_file, 'w') as f:
            json.dump(self.payload, f, indent=4)
    # [END write_payload_to_file]

    # [START insert_dynamic_data_to_dag]
    def insert_dynamic_data_to_dag(self):
        """Inserts dynamic data into the concrete dag file at the position defined by INSERTION_MARKER"""
        self.logger.log(logging.DEBUG, "Inserting the dynamic data into the dag file.")
        # read the concrete dag file and find the insertion marker
        with open(self.dag_file, "r") as f:
            contents = f.readlines()
            for i, line in enumerate(contents):
                if self.INSERTION_MARKER in line:
                    insertion_pos = i + 1
                    break

        """ 
        Inserts the path to the concrete json data file
            with open(os.path.join(os.path.dirname(Path(__file__)), 'json_file.json')) as f:
                payload = json.load(f)
        """
        contents.insert(
            insertion_pos,
            f"with open(os.path.join(os.path.dirname(Path(__file__)), "
            f"'{ntpath.basename(self.json_file)}')) as f:\n"
        )
        contents.insert(insertion_pos+1, f"    payload = json.load(f)")

        # write back the modified contents to the concrete dag file
        with open(self.dag_file, "w") as f:
            f.writelines(contents)
    # [END insert_dynamic_data_to_dag]

    # [START generate_dag]
    def generate_dag(self):
        """
        Generates a concrete dag file with its associated payload data in a concrete json file.
        Returns:
            a tuple containing the path to the dag_file and the path to the json_file
        """
        self.logger.log(logging.DEBUG, "Generating the dag file.")
        self.remove_previous_versions()
        self.copy_dag_template_to_file()
        self.write_payload_to_file()
        self.insert_dynamic_data_to_dag()
        return {'dag_file': self.dag_file, 'json_file': self.json_file}
    # [END generate_dag]
