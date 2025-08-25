import sys
import os

# Add the current directory to the Python path so we can import GAI
plugin_dir = os.path.dirname(os.path.abspath(__file__))
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

# Import the GAI package which contains all the commands
import GAI

# Re-export the commands so Sublime Text can find them
from GAI.commands import generate_text_command
from GAI.commands import replace_text_command
from GAI.commands import edit_gai_plugin_settings_command
from GAI.core import generate_code_generator
from GAI.core import write_code_generator
from GAI.core import complete_code_generator
from GAI.core import whiten_code_generator
from GAI.core import edit_code_generator
from GAI.instruction import instruction_input_handler
