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

# Import from the GAI directory structure
import GAI.config
import GAI.core


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
        cmd = GAI.core.code_generator(mock_view)
        cmd.view = mock_view
        try:
            cmd.validate_setup()
        except ValueError:
            pytest.fail("validate_setup raised ValueError unexpectedly")

    def test_validate_setup_multiple_selections(self, mock_view):
        """validate_setup must raise when more than one region is selected"""
        mock_view.sel.return_value = [Mock(), Mock()]
        cmd = GAI.core.code_generator(mock_view)
        cmd.view = mock_view
        with pytest.raises(ValueError):
            cmd.validate_setup()

    def test_validate_setup_empty_selection(self, mock_view):
        """validate_setup must raise when the sole selection is empty"""
        mock_view.sel.return_value = [Mock(empty=lambda: True)]
        cmd = GAI.core.code_generator(mock_view)
        cmd.view = mock_view
        with pytest.raises(ValueError):
            cmd.validate_setup()


class TestConfigurator:

    @pytest.fixture
    def mock_base_obj(self, mock_view):
        base_obj = Mock()
        base_obj.view = mock_view
        return base_obj

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

        mock_base_obj = Mock()
        config = GAI.config.GAIConfig(source_config, "command_edit", mock_base_obj)
        config.ready_wait = lambda: None
        config.__configuration__completed__ = True

        assert config.get_model() == "gpt-3.5-turbo"
        assert config.get("temperature") == 0.3

    def test_config_merge_with_priority_keys(self, mock_base_obj):
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

        config = GAI.config.GAIConfig(source_config, "command_custom", mock_base_obj)
        config.ready_wait = lambda: None
        config.__configuration__completed__ = True

        # "target_prio_str_keys" should concatenate base + custom prompts
        expected_prompt = "Base prompt\n\nCustom prompt"
        assert config.get_prompt() == expected_prompt

    def test_config_cancelled_via_quick_panel(self, mock_base_obj):
        """Test configurator returns cancelled when user cancels quick panel"""
        source_config = {
            "command_test": {
                "alternates": {"debug": {"model": "debug"}}
            }
        }

        # Simulate the quick panel being shown and the user cancelling (index -1)
        def simulate_cancel(items, on_done):
            on_done(-1)

        # Ensure the view's window().show_quick_panel uses our simulation
        mock_base_obj.view.window.return_value.show_quick_panel.side_effect = simulate_cancel

        config = GAI.config.GAIConfig(source_config, "command_test", mock_base_obj)
        # The configurator runs the quick panel synchronously via the side effect,
        # so we can directly check the cancelled flag.
        assert config.is_cancelled() is True
