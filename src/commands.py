import importlib
# Import the *real* (or mocked) top‑level modules.
sublime = importlib.import_module('sublime')
sublime_plugin = importlib.import_module('sublime_plugin')

from ._base import (
    _base_text_command, 
    _base_application_command
    )
from .config import gai_config
# The async worker module provides the thread class and logger.
from .async_worker import async_code_generator, logger
import json


class gai_replace_text_command(_base_text_command()):
    """
    Simple command that replaces the text in the given region.
    In the real Sublime environment the command is instantiated by the
    editor and receives the view automatically. The unit‑tests instantiate
    the command manually, so we need an ``__init__`` that
    accepts the view and stores it on the instance.
    """
    def __init__(self, view):
        # ``_base_text_command`` may be ``object`` in the test harness,
        # therefore we cannot rely on ``super()`` calling a real base
        # ``__init__``. Simply store the view for later use.
        self.view = view

    def run(self, edit, region, text):
        """
        ``region`` is supplied as a tuple (begin, end). The real Sublime API
        expects a ``sublime.Region`` instance, which is mocked in the test
        suite. Expanding the tuple creates the mock Region object.
        """
        region = sublime.Region(*region)
        self.view.replace(edit, region, text)


class gai_generate_text_command(sublime_plugin.TextCommand):
    """
    Command that generates or edits text via an LLM.
    """
    def __init__(self, view):
        # Handle both real Sublime and test environments
        try:
            super().__init__(view)
        except TypeError:
            # In environment, just store the view
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
        ai_thread = async_code_generator(selected_region, config_handle,
                                         data_handle)
        ai_thread.start()
        self.manage_thread(ai_thread,
                           config_handle.__running_config__.get("max_seconds", 60))

    def manage_thread(self, thread, max_time, seconds=0):
        """
        Manages the running thread and checks it's still running or if it
        has a result.
        """
        window = self.view.window()

        if seconds >= max_time:
            message = "Ran out of time! {}s".format(max_time)
            if window:
                window.status_message(message)
            else:
                sublime.status_message(message)
            return

        if thread.running:
            message = "Thinking, one moment... ({}/{}s)".format(
                seconds, max_time)
            if window:
                window.status_message(message)
            else:
                sublime.status_message(message)
            sublime.set_timeout(lambda:
                                self.manage_thread(thread,
                                                   max_time,
                                                   seconds + 1), 1000)
            return

        if not thread.result:
            message = "Something is wrong, did not receive response - aborting"
            if window:
                window.status_message(message)
            else:
                sublime.status_message(message)
            return

        self.view.run_command('replace_text', {
            "region": [thread.region.begin(), thread.region.end()],
            "text": thread.text_replace + thread.result
        })

    def create_data(self, config_handle, code_region):
        """Build prompt payload."""
        prompt = config_handle.get_prompt()
        persona = config_handle.get_persona()
        model = config_handle.get_model()
        max_tokens = config_handle.get('max_tokens', 100)
        temperature = config_handle.get('temperature', 0)

        # NOTE: f‑strings are not supported in Sublime Text's Python 3.3
        # runtime, so we use .format() for compatibility.
        data = {
            'messages': [
                {'role': 'system', 'content': persona},
                {'role': 'user', 'content': "{}\n{}".format(prompt, code_region)}
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


# The original implementation inherited from ``sublime_plugin.ApplicationCommand``.
# In the test environment ``sublime_plugin`` is a simple ``Mock`` object, and
# inheriting from it can interfere with method resolution.  The command does
# not rely on any behaviour from the base class, so we make it a plain class.
class gai_edit_plugin_settings_command(_base_application_command()):
    """
    Open GAI settings in a new window with split layout.
    """
    def run(self):
        # Open a new window and configure a two‑column layout.
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
