# logging_config.py

import logging

def setup_logging(log_file='src.log', log_level=logging.INFO):
    """Set up the logging configuration."""
    logging.basicConfig(
        filename=log_file,  # Log file name
        level=log_level,  # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
    )
