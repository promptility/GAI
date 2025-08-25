import sublime
import sublime_plugin


# Import all commands and classes directly from their modules
# This makes them available at the top level for Sublime Text
from .GAI.commands import gai_generate_text_command
from .GAI.commands import gai_replace_text_command
from .GAI.commands import gai_edit_plugin_settings_command


def plugin_loaded():
    print("GAI loaded!")

def plugin_unloaded():
    print("GAI unloaded!")

