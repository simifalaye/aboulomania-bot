import logging
import logging.handlers

LOG_FILE_NAME = 'logs/app.log'

"""
Setup logger
"""

def setup_logger():
    logger = logging.getLogger("bot")
    logger.setLevel(logging.INFO)

    # Define the console_handler
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)

    # Define the file handler
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=LOG_FILE_NAME, when='midnight', backupCount=5
    )
    file_handler_formatter = logging.Formatter(
        "[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{")
    file_handler.setFormatter(file_handler_formatter)
    logger.addHandler(file_handler)

    return logger

logger = setup_logger()
