import os
import logging
from unittest import TestCase, main
from composer.utils import log_service


class AuthServiceTests(TestCase):

    @staticmethod
    def test_set_logger_level_debug():
        os.environ['LOG_LEVEL'] = 'DEBUG'
        logger = log_service.get_module_logger(__name__)
        assert logger.level == 10
        assert logging.getLevelName(logger.level) == 'DEBUG'

    @staticmethod
    def test_set_logger_level_info():
        os.environ['LOG_LEVEL'] = 'INFO'
        logger = log_service.get_module_logger(__name__)
        assert logger.level == 20
        assert logging.getLevelName(logger.level) == 'INFO'

    @staticmethod
    def test_set_logger_level_warning():
        os.environ['LOG_LEVEL'] = 'WARNING'
        logger = log_service.get_module_logger(__name__)
        assert logger.level == 30
        assert logging.getLevelName(logger.level) == 'WARNING'

    @staticmethod
    def test_set_logger_level_error():
        os.environ['LOG_LEVEL'] = 'ERROR'
        logger = log_service.get_module_logger(__name__)
        assert logger.level == 40
        assert logging.getLevelName(logger.level) == 'ERROR'

    @staticmethod
    def test_set_logger_level_critical():
        os.environ['LOG_LEVEL'] = 'CRITICAL'
        logger = log_service.get_module_logger(__name__)
        assert logger.level == 50
        assert logging.getLevelName(logger.level) == 'CRITICAL'

    @staticmethod
    def test_set_logger_level_unknown():
        os.environ['LOG_LEVEL'] = 'NOT_KNOWN'
        logger = log_service.get_module_logger(__name__)
        assert logger.level == 10
        assert logging.getLevelName(logger.level) == 'DEBUG'


if __name__ == '__main__':
    main()
