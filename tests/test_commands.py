import pytest
from unittest.mock import Mock, patch
import sys

# --- Mock 'sublime' and 'sublime_plugin' modules before importing GAI ---
sys.modules['sublime'] = Mock(
    run_command=Mock(),
    active_window=Mock()
)
sys.modules['sublime_plugin'] = Mock()

# Import from the GAI directory structure
import GAI.commands


class TestReplaceTextCommand:

    def test_replace_text_command_init(self):
        """Test replace_text_command initialization"""
        mock_view = Mock()
        cmd = GAI.commands.replace_text_command(mock_view)
        assert cmd.view == mock_view

    def test_replace_text_command_run(self):
        """Test replace_text_command run method"""
        mock_view = Mock()
        mock_edit = Mock()
        
        cmd = GAI.commands.replace_text_command(mock_view)
        
        # Mock the Region constructor
        with patch('GAI.commands.sublime.Region') as mock_region:
            mock_region_instance = Mock()
            mock_region.return_value = mock_region_instance
            
            cmd.run(mock_edit, [5, 15], "new text")
            
            # Verify Region was called with correct parameters
            mock_region.assert_called_once_with(5, 15)
            # Verify view.replace was called
            mock_view.replace.assert_called_once_with(mock_edit, mock_region_instance, "new text")


class TestEditGaiPluginSettingsCommand:

    def test_edit_gai_plugin_settings_command_run(self):
        """Test edit_gai_plugin_settings_command run method"""
        cmd = GAI.commands.edit_gai_plugin_settings_command()
        
        # Mock the active_window and other sublime functions
        mock_window = Mock()
        sys.modules['sublime'].active_window = Mock(return_value=mock_window)
        sys.modules['sublime'].run_command = Mock()
        
        cmd.run()
        
        # Verify new_window command was run
        sys.modules['sublime'].run_command.assert_called_once_with('new_window')
        
        # Verify set_layout was called
        mock_window.run_command.assert_any_call('set_layout', {
            'cols': [0.0, 0.5, 1.0],
            'rows': [0.0, 1.0],
            'cells': [[0, 0, 1, 1], [1, 0, 2, 1]]
        })
        
        # Verify focus_group was called
        mock_window.focus_group.assert_any_call(0)
        mock_window.focus_group.assert_any_call(1)
        
        # Verify open_file was called for both files
        mock_window.run_command.assert_any_call(
            'open_file', {'file': '${packages}/GAI/gai.sublime-settings'})
        mock_window.run_command.assert_any_call(
            'open_file', {'file': '${packages}/User/gai.sublime-settings'})
