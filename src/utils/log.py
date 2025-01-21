import logging
from logging.handlers import RotatingFileHandler

def setup_logging(log_level=logging.INFO):
    """
    Sets up the logging system for the application.

    :param log_level: The minimum level of log messages to be emitted.
        Defaults to logging.INFO.
    """
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=1000000, backupCount=5)
    file_handler.setLevel(log_level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    cors_logger = logging.getLogger('flask_cors')
    cors_logger.setLevel(logging.DEBUG)
    cors_logger.addHandler(console_handler)
    cors_logger.addHandler(file_handler)

    return root_logger, cors_logger
