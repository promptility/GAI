import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import threading
import json
import http.client
import logging

# --- Mock 'sublime' and 'sublime_plugin' modules ---
sys.modules['sublime'] = Mock()
sys.modules['sublime_plugin'] = Mock()

# Import from the GAI directory structure
from GAI.async_worker import async_code_generator, logger


class test_async_code_generator:

    @pytest.fixture
    def mock_region(self):
        region = Mock()
        region.begin.return_value = 10
        region.end.return_value = 20
        return region

    @pytest.fixture
    def mock_config_handle(self):
        config = Mock()
        config.get.return_value = "test_value"
        config.is_cancelled.return_value = False
        return config

    @pytest.fixture
    def mock_data_handle(self):
        def data_handle(field):
            if field == "data":
                return {"test": "data"}
            elif field == "text":
                return "test_text"
            return None
        return data_handle

    def test_async_code_generator_init(self, mock_region, mock_config_handle, mock_data_handle):
        """Test async_code_generator initialization"""
        thread = async_code_generator(mock_region, mock_config_handle, mock_data_handle)
        
        assert thread.region == mock_region
        assert thread.config_handle == mock_config_handle
        assert thread.data_handle == mock_data_handle
        assert thread.running is False
        assert thread.result is None

    def test_async_code_generator_run_cancelled(self, mock_region, mock_config_handle, mock_data_handle):
        """Test async_code_generator run when cancelled"""
        mock_config_handle.is_cancelled.return_value = True
        
        thread = async_code_generator(mock_region, mock_config_handle, mock_data_handle)
        thread.run()
        
        assert thread.running is False
        assert thread.result == []

    def test_setup_logs_adds_stream_handler(self):
        """Test setup_logs adds stream handler when needed"""
        # Mock the logging classes properly
        with patch('logging.StreamHandler') as mock_stream_handler_class, \
             patch('logging.getLogger') as mock_get_logger:
            
            # Create actual mock StreamHandler instance
            mock_stream_handler = MagicMock()
            mock_stream_handler_class.return_value = mock_stream_handler
            
            # Create mock logger with empty handlers
            mock_logger = Mock()
            mock_logger.handlers = []
            mock_get_logger.return_value = mock_logger
            
            mock_config = Mock()
            mock_config.get.side_effect = lambda key, default=None: "debug" if key == "log_level" else default
            
            # Create thread and call setup_logs
            thread = async_code_generator(Mock(), mock_config, Mock())
            thread.setup_logs()
            
            # Verify stream handler was added - check if StreamHandler was instantiated
            mock_stream_handler_class.assert_called()

    def test_setup_logs_adds_file_handler(self):
        """Test setup_logs adds file handler when needed"""
        with patch('logging.FileHandler') as mock_file_handler_class, \
             patch('logging.getLogger') as mock_get_logger:
            
            # Create actual mock FileHandler instance
            mock_file_handler = MagicMock()
            mock_file_handler_class.return_value = mock_file_handler
            
            # Create mock logger with empty handlers
            mock_logger = Mock()
            mock_logger.handlers = []
            mock_get_logger.return_value = mock_logger
            
            mock_config = Mock()
            mock_config.get.return_value = "test.log"  # File path
            
            # Create thread and call setup_logs
            thread = async_code_generator(Mock(), mock_config, Mock())
            thread.setup_logs()
            
            # Verify file handler was added - check if FileHandler was instantiated
            assert mock_file_handler_class.call_count >= 1

    def test_get_max_seconds(self, mock_region, mock_config_handle, mock_data_handle):
        """Test get_max_seconds method"""
        mock_config_handle.get.return_value = 120
        
        thread = async_code_generator(mock_region, mock_config_handle, mock_data_handle)
        max_seconds = thread.get_max_seconds()
        
        mock_config_handle.get.assert_called_with("max_seconds", 60)
        assert max_seconds == 120
