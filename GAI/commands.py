import importlib
# Import the *real* (or mocked) top‑level modules.
sublime = importlib.import_module('sublime')
sublime_plugin = importlib.import_module('sublime_plugin')

from ._base import _base_text_command
from .config import gai_config
from .async_worker import async_code_generator, logger
import json

class GaiReplaceTextCommand(_base_text_command()):
    """
    Simple command that replaces the text in the given region.
    In the real Sublime environment the command is instantiated by the
    editor and receives the view automatically.  In the unit‑tests we
    instantiate the command manually, so we need an ``__init__`` that
    accepts the view and stores it on the instance.
    """
    def __init__(self, view):
        # ``_base_text_command`` may be ``object`` in the test harness,
        # therefore we cannot rely on ``super()`` calling a real base
        # ``__init__``.  Simply store the view for later use.
        self.view = view

    def run(self, edit, region, text):
        # ``region`` is supplied as a tuple (begin, end).  The real
        # Sublime API expects a ``sublime.Region`` instance, which is
        # mocked in the test suite.  Expanding the tuple creates the
        # mock Region object.
        region = sublime.Region(*region)
        self.view.replace(edit, region, text)


class GaiGenerateTextCommand(_base_text_command()):
    """
    Command that generates or edits text via an LLM.
    """
    def __init__(self, view):
        # Handle both real Sublime and test environments
        try:
            super().__init__(view)
        except TypeError:
            # In test environment, just store the view
            pass
        self.view = view

    def run(self, edit):
        self.validate_setup()
        self.base_execute(edit)

    def validate_setup(self):
        """Ensure exactly one selection exists."""
        if len(self.view.sel()) != 1:
            sublime.status_message("Please highlight exactly one code segment.")
            raise ValueError("Multiple or no selections.")
        if self.view.sel()[0].empty():
            sublime.status_message("No text selected.")
            raise ValueError("Empty selection.")

    def base_execute(self, edit):
        """Launch async generator and manage the thread."""
        configurations = sublime.load_settings('gai.sublime-settings')
        config_handle = gai_config(configurations, "command_generate", self)
        config_handle.ready_wait()

        selected_region = self.view.sel()[0]
        code_region = self.view.substr(selected_region)

        data_handle = self.create_data(config_handle, code_region)
        codex_thread = async_code_generator(selected_region, config_handle,
                                            data_handle)
        codex_thread.start()
        self.manage_thread(codex_thread,
                           config_handle.__running_config__.get("max_seconds", 60))

    def create_data(self, config_handle, code_region):
        """Build prompt payload."""
        prompt = config_handle.get_prompt()
        persona = config_handle.get_persona()
        model = config_handle.get_model()
        max_tokens = config_handle.get('max_tokens', 100)
        temperature = config_handle.get('temperature', 0)

        data = {
            'messages': [
                {'role': 'system', 'content': persona},
                {'role': 'user', 'content': f"{prompt}\n{code_region}"}
            ],
            'model': model,
            'max_tokens': max_tokens,
            'temperature': temperature
        }

        log_level = config_handle.get("log_level", "requests")
        if log_level in ["requests", "all"]:
            logger.info("Request Data: %s", json.dumps(data, indent=4))

        def await_result(field):
            return data[field]

        return await_result


class GaiEditPluginSettingsCommand(
        sublime_plugin.ApplicationCommand
        if isinstance(sublime_plugin.ApplicationCommand, type)
        else object):
    def run(self):
        """Open GAI settings in a new window with split layout."""
        sublime.run_command('new_window')
        new_window = sublime.active_window()
        new_window.run_command('set_layout', {
            'cols': [0.0, 0.5, 1.0],
            'rows': [0.0, 1.0],
            'cells': [[0, 0, 1, 1], [1, 0, 2, 1]]
        })
        new_window.focus_group(0)
        new_window.run_command(
            'open_file', {'file': '${packages}/GAI/gai.sublime-settings'})
        new_window.focus_group(1)
        new_window.run_command(
            'open_file', {'file': '${packages}/User/gai.sublime-settings'})
