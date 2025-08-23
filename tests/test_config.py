import pytest
from unittest.mock import Mock, call
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

    def test_config_shows_quick_panel_when_no_default_alternate(self, mock_base_obj):
        """Test that quick panel is shown when no default alternate is configured"""
        source_config = {
            "command_test": {
                "alternates": {
                    "fast": {"model": "gpt-3.5-turbo"},
                    "smart": {"model": "gpt-4"}
                }
            }
        }

        config = GAI.config.GAIConfig(source_config, "command_test", mock_base_obj)
        
        # Verify that show_quick_panel was called with the correct parameters
        # Note: The order of items in the list is ["default", "fast", "smart"] based on dict keys
        mock_base_obj.view.window.return_value.show_quick_panel.assert_called_once()
        call_args = mock_base_obj.view.window.return_value.show_quick_panel.call_args
        items = call_args[0][0]  # First positional argument
        assert items == ["default", "fast", "smart"] or items == ["default", "smart", "fast"]

    def test_config_does_not_show_quick_panel_when_default_alternate_exists(self, mock_base_obj):
        """Test that quick panel is not shown when default alternate is configured"""
        source_config = {
            "command_test": {
                "alternates": {
                    "default": "fast",
                    "fast": {"model": "gpt-3.5-turbo"},
                    "smart": {"model": "gpt-4"}
                }
            }
        }

        config = GAI.config.GAIConfig(source_config, "command_test", mock_base_obj)
        
        # Verify that show_quick_panel was NOT called
        mock_base_obj.view.window.return_value.show_quick_panel.assert_not_called()
        
        # Verify configuration is completed immediately
        assert config.__configuration__completed__ is True

    def test_config_merge_with_input_prio_str_keys(self, mock_base_obj):
        """Test string merge with input priority keys"""
        source_config = {
            "__meta__": {
                "input_prio_str_keys": ["prompt"]
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

        # "input_prio_str_keys" should concatenate custom + base prompts
        expected_prompt = "Custom prompt\n\nBase prompt"
        assert config.get_prompt() == expected_prompt

    def test_config_merge_with_input_prio_keys(self, mock_base_obj):
        """Test merge with input priority keys"""
        source_config = {
            "__meta__": {
                "input_prio_keys": ["model"]
            },
            "oai": {
                "model": "gpt-3.5"
            },
            "command_custom": {
                "model": "gpt-4"
            }
        }

        config = GAI.config.GAIConfig(source_config, "command_custom", mock_base_obj)
        config.ready_wait = lambda: None
        config.__configuration__completed__ = True

        # "input_prio_keys" should use input value
        assert config.get_model() == "gpt-4"

    def test_config_merge_with_dict_and_scalar_values(self, mock_base_obj):
        """Test merge with dict and scalar values"""
        source_config = {
            "oai": {
                "settings": {"temperature": 0.5}
            },
            "command_custom": {
                "settings": "default"
            }
        }

        config = GAI.config.GAIConfig(source_config, "command_custom", mock_base_obj)
        config.ready_wait = lambda: None
        config.__configuration__completed__ = True

        # Dict and scalar should be merged with scalar as value for key
        # This is a complex merge case, just check it doesn't crash
        assert config.get("settings") is not None

    def test_config_get_with_default_values(self, mock_base_obj):
        """Test get methods with default values"""
        source_config = {
            "command_test": {}
        }

        config = GAI.config.GAIConfig(source_config, "command_test", mock_base_obj)
        config.ready_wait = lambda: None
        config.__configuration__completed__ = True

        # Test default values
        assert config.get_prompt() == ""
        assert config.get_persona() == "You are a helpful AI Assistant"
        assert config.get_model() == "gpt-4"
        assert config.get("nonexistent", "default") == "default"

    def test_config_ready_wait_sleeps_until_completed(self, mock_base_obj):
        """Test ready_wait sleeps until configuration is completed"""
        import time
        source_config = {
            "command_test": {
                "alternates": {
                    "fast": {"model": "gpt-3.5-turbo"}
                }
            }
        }

        config = GAI.config.GAIConfig(source_config, "command_test", mock_base_obj)
        
        # Simulate completion after a short delay
        def complete_config():
            time.sleep(0.1)
            config.__configuration__completed__ = True

        import threading
        thread = threading.Thread(target=complete_config)
        thread.start()
        
        # This should block until completion
        config.ready_wait(0.05)  # Use shorter sleep duration for test
        assert config.__configuration__completed__ is True

    def test_config_user_selects_alternate(self, mock_base_obj):
        """Test user selects an alternate configuration"""
        source_config = {
            "command_test": {
                "alternates": {
                    "fast": {"model": "gpt-3.5-turbo", "temperature": 0.3},
                    "smart": {"model": "gpt-4", "temperature": 0.7}
                }
            }
        }

        # Capture the on_select callback to simulate user selection
        on_select_callback = None
        
        def capture_callback(items, on_select=None, **kwargs):
            nonlocal on_select_callback
            on_select_callback = on_select
            
        mock_base_obj.view.window.return_value.show_quick_panel.side_effect = capture_callback

        config = GAI.config.GAIConfig(source_config, "command_test", mock_base_obj)
        
        # Now simulate the user selecting index 1 ("fast" - but we need to check the actual order)
        if on_select_callback:
            # Get the actual items that were passed to show_quick_panel
            call_args = mock_base_obj.view.window.return_value.show_quick_panel.call_args
            items = call_args[0][0]
            
            # Find the index of "fast" in the actual list
            fast_index = items.index("fast")
            on_select_callback(fast_index)  # Select "fast"
        
        # Configuration should be completed
        assert config.__configuration__completed__ is True
        # Should not be cancelled
        assert config.is_cancelled() is False
        # Should have selected the "fast" configuration
        assert config.get_model() == "gpt-3.5-turbo"
        assert config.get("temperature") == 0.3
