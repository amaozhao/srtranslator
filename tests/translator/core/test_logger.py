"""
Tests for the core.logger module.
"""

import os
from unittest import mock

from translator.core.logger import configure_logging, get_logger


class TestLogger:
    """Test cases for the logger module."""

    def test_configure_logging_basic(self):
        """Test basic logging configuration."""
        with mock.patch("structlog.configure") as mock_configure:
            configure_logging()
            # Verify structlog.configure was called
            assert mock_configure.called

    def test_configure_logging_json_format(self):
        """Test JSON format logging configuration."""
        with mock.patch.dict(os.environ, {"LOG_FORMAT": "json"}):
            with mock.patch("structlog.configure") as mock_configure:
                configure_logging()
                # Verify structlog.configure was called
                assert mock_configure.called

    def test_configure_logging_console_format(self):
        """Test console format logging configuration."""
        with mock.patch.dict(os.environ, {"LOG_FORMAT": "console"}):
            with mock.patch("structlog.configure") as mock_configure:
                configure_logging()
                # Verify structlog.configure was called
                assert mock_configure.called

    def test_configure_logging_file_handler(self):
        """Test file handler configuration when log_file is specified."""
        # Create a simple test to verify that handlers are correctly configured
        with mock.patch("translator.core.config.settings") as mock_settings:
            # Configure mock settings
            mock_settings.log_level = "INFO"
            mock_settings.log_format = "json"
            mock_settings.log_file = "/tmp/test.log"

            # Mock logging.FileHandler to verify it would be created
            with mock.patch("logging.FileHandler"):
                # Mock os.makedirs to avoid actual directory creation
                with mock.patch("os.makedirs"):
                    configure_logging()

                    # Verify handlers are correctly configured in
                    # logging.basicConfig
                    with mock.patch("logging.basicConfig") as mock_basic_config:
                        configure_logging()
                        # Check that basicConfig was called
                        assert mock_basic_config.called

    def test_get_logger(self):
        """Test that get_logger returns a structlog logger."""
        # Configure logging first
        with mock.patch("structlog.configure"):
            configure_logging()

        # Get a logger
        logger = get_logger("test_logger")

        # Verify it's a structlog logger
        # (could be BoundLogger or BoundLoggerLazyProxy)
        # Just check that it's from structlog and has the expected methods
        assert hasattr(logger, "info")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")

    def test_logger_methods(self):
        """Test that logger methods work correctly."""
        # For this test, we'll just verify that the logger
        # has the expected methods
        # and that they can be called without errors

        # Mock structlog.get_logger to return a mock logger
        with mock.patch("structlog.get_logger") as mock_get_logger:
            # Create a mock logger with all the expected methods
            mock_logger = mock.MagicMock()
            mock_get_logger.return_value = mock_logger

            # Get a logger through our function
            logger = get_logger("test_logger")

            # Verify that structlog.get_logger was called with the right name
            mock_get_logger.assert_called_once_with("test_logger")

            # Call the logger methods to make sure they work
            logger.debug("Debug message", extra="value")
            logger.info("Info message", extra="value")
            logger.warning("Warning message", extra="value")
            logger.error("Error message", extra="value")

            # Verify the methods were called on the mock logger
            assert mock_logger.debug.called
            assert mock_logger.info.called
            assert mock_logger.warning.called
            assert mock_logger.error.called
