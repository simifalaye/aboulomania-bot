import os
import sys
import json

from helpers.logger import logger

def check_required(config: dict, field: str, type: type):
    """Ensure a required field is present and has the correct type

    Args:
        config: config
        field: dict field to check
        type: type of field
    """
    if field not in config or not config[field] or not isinstance(config[field], type):
        logger.error("Application started with invalid '{}' provided.".format(field))
        sys.exit("'config.json' MUST contain a valid '{}'.".format(field))

def set_default(config: dict, field: str, type: type, default):
    """Check if field is present and has correct type or use default

    Args:
        default (any): default value
        config: config
        field: dict field to check
        type: type of field
    """
    if field not in config or not config[field] or not isinstance(config[field], type):
        config[field] = default

"""
Load config file
"""
config_file = f"{os.path.realpath(os.path.dirname(__file__))}/../config.json"
if not os.path.isfile(config_file):
    logger.error("Application started with no config file.")
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(config_file) as file:
        config = json.load(file)
        # Check required fields
        check_required(config, "token", str)
        check_required(config, "permissions", str)
        check_required(config, "application_id", str)

        # Set defaults
        set_default(config, "prefix", str, "!")
        set_default(config, "timezone", str, "Canada/Saskatchewan")
        set_default(config, "owners", list, [])
        set_default(config, "auto_draw_weekday", int, 2)
        set_default(config, "auto_draw_hour", int, 19)
