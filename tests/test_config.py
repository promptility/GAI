import pytest
from unittest.mock import Mock
import sys

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


class TestConfigurator:

    @pytest.fixture
    def mock_base_obj(self, mock_view):
        base_obj = Mock()
        base_obj.view = mock_view
        return base_obj

    def test_config_merge_with_alternates_default(self, mock_base_obj):
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
        # Updated to accept the new parameter format with on_select
        def simulate_cancel(items, on_select=None, **kwargs):
            if on_select is not None:
                on_select(-1)
            else:
                # Fallback for other parameter formats
                on_done = kwargs.get('on_done')
                if on_done is not None:
                    on_done(-1)

        # Ensure the view's window().show_quick_panel uses our simulation
        mock_base_obj.view.window.return_value.show_quick_panel.side_effect = simulate_cancel

        config = GAI.config.GAIConfig(source_config, "command_test", mock_base_obj)
        # The configurator runs the quick panel synchronously via the side effect,
        # so we can directly check the cancelled flag.
        assert config.is_cancelled() is True
