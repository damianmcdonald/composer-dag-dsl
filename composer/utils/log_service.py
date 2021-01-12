#!/usr/bin/env python

"""log_service.py: Service module that provides logging functionalities"""

__author__ = "Damian McDonald"
__credits__ = ["Damian McDonald"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Damian McDonald"
__status__ = "Development"

import logging
import os


# [START get_module_logger]
def get_module_logger(module_name):
    """
    Gets logging configuration for a module name.
    Args:
        module_name (string): the name of the module for the logger
    Returns:
        an instance of logging.Logger
    """

    logger = logging.getLogger(module_name)

    # check if LOG_LEVEL env var is defined
    if 'LOG_LEVEL' in os.environ:
        log_level = os.environ['LOG_LEVEL']
        if log_level == "DEBUG":
            log_level = logging.DEBUG
        elif log_level == "INFO":
            log_level = logging.INFO
        elif log_level == "WARNING":
            log_level = logging.WARNING
        elif log_level == "ERROR":
            log_level = logging.ERROR
        elif log_level == "CRITICAL":
            log_level = logging.CRITICAL
        else:
            log_level = logging.DEBUG
    else:
        # Set default log level
        log_level = logging.DEBUG

    # set the logging configuration
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(log_level)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    # set overall log level
    logger.setLevel(log_level)

    return logger
# [END get_module_logger]
