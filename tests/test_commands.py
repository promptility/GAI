import pytest
from unittest.mock import Mock, patch
import sys

# --- Mock 'sublime' and 'sublime_plugin' modules before importing GAI ---
mock_sublime = Mock()
mock_sublime.active_window = Mock()
mock_sublime.run_command = Mock()

sys.modules['sublime'] = mock_sublime
sys.modules['sublime_plugin'] = Mock()

# Import from the GAI directory structure
import GAI.commands


class Test_replace_text_command:

    def test_replace_text_command_init(self):
        """Test replace_text_command initialization"""
        mock_view = Mock()
        cmd = GAI.commands.gai_replace_text_command(mock_view)
        assert cmd.view == mock_view

    def test_replace_text_command_run(self):
        """Test replace_text_command run method"""
        mock_view = Mock()
        mock_edit = Mock()
        
        cmd = GAI.commands.gai_replace_text_command(mock_view)
        
        # Mock the Region constructor
        with patch('GAI.commands.sublime.Region') as mock_region:
            mock_region_instance = Mock()
            mock_region.return_value = mock_region_instance
            
            cmd.run(mock_edit, [5, 15], "new text")
            
            # Verify Region was called with correct parameters
            mock_region.assert_called_once_with(5, 15)
            # Verify view.replace was called
            mock_view.replace.assert_called_once_with(mock_edit, mock_region_instance, "new text")


class Test_edit_gai_plugin_settings_command:

    def test_edit_gai_plugin_settings_command_run(self):
        """Test edit_gai_plugin_settings_command run method"""
        cmd = GAI.commands.gai_edit_plugin_settings_command()
        
        # Mock the entire sublime module
        with patch('GAI.commands.sublime') as mock_sublime_module:
            mock_new_window = Mock()
            mock_sublime_module.active_window.return_value = mock_new_window
            mock_sublime_module.run_command = Mock()
            
            cmd.run()
            
            # Verify set_layout was called on the new window
            mock_new_window.run_command.assert_any_call('set_layout', {
                'cols': [0.0, 0.5, 1.0],
                'rows': [0.0, 1.0],
                'cells': [[0, 0, 1, 1], [1, 0, 2, 1]]
            })
            
            # Verify focus_group was called
            mock_new_window.focus_group.assert_any_call(0)
            mock_new_window.focus_group.assert_any_call(1)
            
            # Verify open_file was called for both files
            mock_new_window.run_command.assert_any_call(
                'open_file', {'file': '${packages}/GAI/gai.sublime-settings'})
            mock_new_window.run_command.assert_any_call(
                'open_file', {'file': '${packages}/User/gai.sublime-settings'})


class Test_generate_text_command:

    def test_generate_text_command_init(self):
        """Test generate_text_command initialization"""
        mock_view = Mock()
        cmd = GAI.commands.gai_generate_text_command(mock_view)
        assert cmd.view == mock_view

    def test_generate_text_command_run(self):
        """Test generate_text_command run method"""
        mock_view = Mock()
        mock_edit = Mock()
        
        cmd = GAI.commands.gai_generate_text_command(mock_view)
        
        # Mock the methods directly on the command instance
        cmd.validate_setup = Mock()
        cmd.base_execute = Mock()
        
        cmd.run(mock_edit)
        
        # Verify validate_setup and base_execute were called
        cmd.validate_setup.assert_called_once()
        cmd.base_execute.assert_called_once_with(mock_edit)
