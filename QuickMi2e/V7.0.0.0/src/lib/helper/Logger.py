"""Logger setup and configuration module."""

import logging
import os
import sys


class LoggerSetup:
    """A dedicated class to set up and configure the logger."""

    def __init__(self, log_name='ModuleGenerator',
                 log_dir_relative_path=r"output\Log"):
        """
        Initialize the logger and ensure the log directory exists.

        Args:
            log_name: Name of the logger (default: 'ModuleGenerator')
            log_dir_relative_path: Relative path to log directory
        """
        self.log_name = log_name
        self.log_dir_relative_path = log_dir_relative_path
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """
        Set up the logger to log actions to a file and console.

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(self.log_name)
        logger.setLevel(logging.INFO)

        # Construct log path
        log_dir = os.path.join(os.getcwd(), self.log_dir_relative_path)
        os.makedirs(log_dir, exist_ok=True)  # Ensure directory exists
        log_file = os.path.join(log_dir, f'{self.log_name.lower()}.log')

        # Create handlers
        file_handler = logging.FileHandler(log_file)
        console_handler = logging.StreamHandler(sys.stdout)

        # Create formatters and set them to handlers
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to the logger (avoiding duplicate handlers)
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger

    def get_logger(self):
        """
        Return the configured logger instance.

        Returns:
            Logger instance
        """
        return self.logger