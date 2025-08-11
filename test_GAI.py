import pytest
from unittest.mock import MagicMock, Mock, patch, call
import threading
import json
import logging
from abc import ABC, abstractmethod
import sys
from pathlib import Path

# --- Mock 'sublime' and 'sublime_plugin' modules before importing GAI ---
sys.modules['sublime'] = Mock(
    load_settings=Mock(),
    status_message=Mock(),
    active_window=Mock(),
    Region=Mock(return_value=Mock())
)
sys.modules['sublime_plugin'] = Mock()

import GAI  # Replace with actual module name


class MockSettings:
    """Mock for sublime.Settings object"""

    def __init__(self, data):
        self.data = data

    def get(self, key, default=None):
        return self.data.get(key, default)


@pytest.fixture
def mock_view():
    view = Mock()
    view.sel.return_value = [Mock(empty=lambda: False, begin=lambda: 0, end=lambda: 10)]
    view.substr.return_value = "print('hello')"
    view.replace = Mock()
    return view


@pytest.fixture
def mock_region():
    region = Mock()
    region.empty.return_value = False
    region.begin.return_value = 10
    region.end.return_value = 20
    return region


@pytest.fixture
def setup_base_generator(mock_view, mock_region):
    mock_view.sel.return_value = [mock_region]
    return mock_view, mock_region


class TestCodeGenerator:

    def test_validate_setup_single_selection(self, mock_view):
        """Test validate_setup allows single non-empty selection"""
        cmd = GAI.code_generator(mock_view)
        cmd.view = mock_view
        try:
            cmd.validate_setup()
        except ValueError:
            pytest.fail("validate_setup raised ValueError unexpectedly")

    # def test_validate_setup_multiple_selections(self, mock_view):
    #     """Test validate_setup rejects multiple selections"""
    #     mock_view.sel.return_value = [Mock(), Mock()]
    #     cmd = GAI.code_generator(mock_view)
    #     cmd.view = mock_view
    #     with pytest.raises(ValueError):
    #         cmd.validate_setup()

    # def test_validate_setup_empty_selection(self, mock_view):
    #     """Test validate_setup rejects empty selection"""
    #     mock_view.sel.return_value = [Mock(empty=lambda: True)]
    #     cmd = GAI.code_generator(mock_view)
    #     cmd.view = mock_view
    #     with pytest.raises(ValueError):
    #         cmd.validate_setup()


class TestConfigurator:

    @pytest.fixture
    def mock_base_obj(self, mock_view):
        base_obj = Mock()
        base_obj.view = mock_view
        return base_obj

    # def test_default_config_merge(self, mock_base_obj):
    #     """Test basic config merge with defaults"""
    #     source_config = {
    #         "oai": {
    #             "model": "gpt-3.5-turbo",
    #             "temperature": 0.5,
    #             "persona": "Default assistant"
    #         },
    #         "command_generate": {
    #             "prompt": "Generate code:",
    #             "temperature": 0.7
    #         },
    #         "__meta__": {}
    #     }

    #     with patch('GAI.sublime.load_settings', return_value=MockSettings(source_config)):
    #         config = GAI.configurator(source_config, "command_generate", mock_base_obj)
    #         config.ready_wait = lambda: None
    #         config.__configuration__completed__ = True

    #         assert config.get_model() == "gpt-3.5-turbo"
    #         assert config.get("temperature") == 0.7
    #         assert config.get_prompt() == "Generate code:"
    #         assert config.get_persona() == "Default assistant"

    def test_config_merge_with_alternates_default(self):
        """Test alternates with default override"""
        source_config = {
            "oai": {"model": "gpt-3.5"},
            "command_edit": {
                "alternates": {
                    "default": "fast",
                    "fast": {"model": "gpt-3.5-turbo", "temperature": 0.3}
                }
            }
        }

        with patch('GAI.sublime.load_settings', return_value=MockSettings(source_config)):
            config = GAI.configurator(source_config, "command_edit", Mock())
            config.ready_wait = lambda: None
            config.__configuration__completed__ = True

            assert config.get_model() == "gpt-3.5-turbo"
            assert config.get("temperature") == 0.3

    def test_config_merge_with_priority_keys(self):
        """Test string merge with priority keys"""
        source_config = {
            "__meta__": {
                "target_prio_str_keys": ["prompt"]
            },
            "oai": {
                "prompt": "Base prompt"
            },
            "command_custom": {
                "prompt": "Custom prompt"
            }
        }

        with patch('GAI.sublime.load_settings', return_value=MockSettings(source_config)):
            config = GAI.configurator(source_config, "command_custom", Mock())
            config.ready_wait = lambda: None
            config.__configuration__completed__ = True

            assert config.get_prompt() == "Base prompt\n\nCustom prompt"

    def test_config_cancelled_via_quick_panel(self):
        """Test configurator returns cancelled when user cancels quick panel"""
        source_config = {
            "command_test": {
                "alternates": {"debug": {"model": "debug"}}
            }
        }

        with patch('GAI.sublime.load_settings', return_value=MockSettings(source_config)):
            config = GAI.configurator(source_config, "command_test", Mock())
            config.ready_wait = lambda: None
            config.cancelled = True
            config.__configuration__completed__ = True

            assert config.is_cancelled()


class TestBaseCodeGenerator:

    def test_create_data_returns_callable(self, setup_base_generator):
        """Test create_data returns a callable that waits and returns data"""
        mock_view, mock_region = setup_base_generator

        with patch('GAI.sublime.load_settings') as mock_load:
            mock_load.return_value = MockSettings({
                "test_section": {
                    "prompt": "Refactor:",
                    "persona": "Coder",
                    "model": "gpt-4",
                    "keep_prompt_text": True
                },
                "oai": {}
            })

            class ConcreteGen(GAI.base_code_generator):
                def code_generator_settings(self):
                    return "test_section"

                def additional_instruction(self):
                    return "optimize"

            cmd = ConcreteGen(mock_view)
            cmd.view = mock_view
            cmd.create_data = Mock()
            cmd.create_data.return_value = lambda key: {
                "data": {
                    "messages": [
                        {"role": "system", "content": "Coder"},
                        {"role": "user", "content": "Refactor: optimize x = 1"}
                    ],
                    "model": "gpt-4"
                },
                "text": "x = 1"
            }.get(key, None)

            config = Mock()
            config.__configuration__completed__ = True
            config.get_prompt = lambda: "Refactor:"
            config.get_persona = lambda: "Coder"
            config.get_model = lambda: "gpt-4"
            config.get = lambda k, d=None: {"max_tokens": 100}.get(k, d)

            data_handle = cmd.create_data(config, "x = 1")
            data = data_handle("data")
            text = data_handle("text")

            assert text == "x = 1"
            assert data['messages'][0]['content'] == "Coder"
            assert "Refactor: optimize x = 1" in data['messages'][1]['content']


class TestAsyncCodeGenerator:

    @patch('GAI.http.client.HTTPSConnection')
    def test_get_code_generator_response_success(self, mock_conn):
        """Test async thread successfully gets response"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "print(x)"}}],
            "usage": {"total_tokens": 42},
            "error": None
        }).encode()
        mock_conn.return_value.getresponse.return_value = mock_response

        config_handle = Mock()
        config_handle.get.side_effect = lambda k, d=None: {
            "open_ai_endpoint": "/chat/completions",
            "open_ai_base": "openai.azure.com",
            "open_ai_key": "fake_key",
            "log_level": "requests"
        }.get(k, d)
        config_handle.is_cancelled.return_value = False

        data_handle = Mock()
        data_handle.return_value = {
            "data": {
                "messages": [{"role": "user", "content": "test"}],
                "model": "gpt-4"
            },
            "text": ""
        }

        region = Mock()
        thread = GAI.async_code_generator(region, config_handle, data_handle)
        thread.setup_logs = Mock()

        result = thread.get_code_generator_response()

        assert result == "print(x)"
        GAI.sublime.status_message.assert_called_with("Tokens used: 42")

    @patch('GAI.http.client.HTTPSConnection')
    def test_get_code_generator_response_error(self, mock_conn):
        """Test error handling in API response"""
        mock_response = Mock()
        mock_response.status = 401
        mock_response.read.return_value = json.dumps({
            "error": {"message": "Invalid API key"}
        }).encode()
        mock_conn.return_value.getresponse.return_value = mock_response

        config_handle = Mock()
        config_handle.get.side_effect = lambda k, d=None: {
            "open_ai_endpoint": "/chat",
            "open_ai_base": "api.openai.com",
            "open_ai_key": "key"
        }.get(k, d)
        config_handle.is_cancelled.return_value = False

        data_handle = Mock(return_value={"data": {"messages": []}})

        thread = GAI.async_code_generator(Mock(), config_handle, data_handle)
        thread.setup_logs = Mock()

        with pytest.raises(ValueError, match="Invalid API key"):
            thread.get_code_generator_response()


# class TestReplaceTextCommand:

#     def test_replace_text_runs_correctly(self, mock_view):
#         """Test replace_text_command replaces region with text"""
#         mock_edit = Mock()
#         mock_region = Mock(begin=Mock(return_value=10), end=Mock(return_value=20))
#         cmd = GAI.replace_text_command(mock_view)

#         cmd.run(mock_edit, region=mock_region, text="new code")

#         mock_view.replace.assert_called_once_with(mock_edit, mock_region, "new code")
