import importlib
# Import the *real* (or mocked) top‑level modules.
sublime = importlib.import_module('sublime')
sublime_plugin = importlib.import_module('sublime_plugin')

import json  # Added import for json usage
import threading  # Added import for threading usage
from abc import abstractmethod  # Needed for abstract methods

from ._base import _base_text_command
# Importing via ``GAI`` caused a circular import because ``GAI.__init__`` imports
# this ``core`` module.  Importing directly from ``.config`` breaks the cycle.
from .config import configurator

# Import async worker and logger to avoid undefined names
from .async_worker import async_code_generator, logger
# Import the instruction input handler used by the edit command
from .instruction import instruction_input_handler


class code_generator(_base_text_command()):
    """
    A class used to generate code using OpenAI.

    Methods
    -------
    validate_setup():
        Validates the setup by checking the API key and the selected region of
        text.

    manage_thread(thread, seconds=0):
        Manages the running thread and checks if it's still running or if it
        has a result.
    """

    def __init__(self, view):
        """
        The real Sublime Text ``TextCommand`` receives the view in its
        constructor.  When we inherit from ``object`` (as the tests do)
        we need to store the view ourselves.
        """
        try:
            super().__init__(view)   # pragma: no‑cover
        except Exception:           # pragma: no‑cover
            pass
        self.view = view

    def validate_setup(self):
        """
        Validates the setup by checking there is a selected region of text.
        """

        if len(self.view.sel()) > 1:
            message = "Please highlight only one code segment."
            sublime.status_message(message)
            raise ValueError(message)

        selected_region = self.view.sel()[0]
        if selected_region.empty():
            message = "No section of text highlighted."
            sublime.status_message(message)
            raise ValueError(message)

    def manage_thread(self, thread, max_time, seconds=0):
        """
        Manages the running thread and checks it's still running or if it
        has a result.

        Parameters
        ----------
        thread : Thread
            The thread to manage.
        seconds : int, optional
            The number of seconds the thread has been running, by default 0.
        """

        if seconds > max_time:
            message = "Ran out of time! {}s".format(max_time)
            sublime.status_message(message)
            return

        if thread.running:
            message = "Thinking, one moment... ({}/{}s)".format(
                seconds, max_time)
            sublime.status_message(message)
            sublime.set_timeout(lambda:
                                self.manage_thread(thread,
                                                   max_time,
                                                   seconds + 1), 1000)
            return

        if not thread.result:
            sublime.status_message(
                "Something is wrong, did not receive response - aborting")
            return

        self.view.run_command('replace_text', {
            "region": [thread.region.begin(), thread.region.end()],
            "text": thread.text_replace + thread.result
        })


class base_code_generator(code_generator):
    """
    A base class for generating code. This class should be inherited by
    specific code generator classes.
    """
    def base_execute(self, edit):

        self.validate_setup()

        configurations = sublime.load_settings('gai.sublime-settings')
        section_name = self.code_generator_settings()

        config_handle = configurator(configurations, section_name, self)
        # Wait for any quick‑panel selection (or default alternate) to finish
        config_handle.ready_wait()

        selected_region = self.view.sel()[0]
        code_region = self.view.substr(selected_region)

        data_handle = self.create_data(config_handle, code_region)

        codex_thread = async_code_generator(selected_region, config_handle,
                                            data_handle)
        codex_thread.start()
        self.manage_thread(codex_thread, config_handle.__running_config__.get(
                           "max_seconds", 60))

    def create_data(self, config_handle, code_region):

        data_container = {"text": None, "data": None}

        def async_prepare():
            code_prompt = config_handle.get_prompt()
            code_instruction = self.additional_instruction()
            user_code_content = "{} {} {}".format(
                code_prompt, code_instruction, code_region)

            data = {
                'messages': [{
                    'role': 'system',
                    'content': config_handle.get_persona(),
                }, {
                    'role': 'user',
                    'content': user_code_content
                }],
                'model': config_handle.get_model(),
                'max_tokens': config_handle.get('max_tokens', 100),
                'temperature': config_handle.get('temperature', 0),
                'top_p': config_handle.get('top_p', 1)
            }

            text = ""
            if config_handle.get('keep_prompt_text', False):
                text = code_region

            data_container["data"] = data
            data_container["text"] = text

            log_level = config_handle.get("log_level", "requests")
            if log_level in ["requests", "all"]:
                logger.info("Request Data: %s", json.dumps(data, indent=4))

        prepthread = threading.Thread(target=async_prepare)
        prepthread.start()

        def await_result(field):
            prepthread.join()
            return data_container.get(field)

        return await_result

    @abstractmethod
    def code_generator_settings(self):
        pass

    @abstractmethod
    def additional_instruction(self):
        return ""


class generate_code_generator(base_code_generator):

    def run(self, edit):
        super().base_execute(edit)

    def code_generator_settings(self):
        return "command_generate"


class write_code_generator(base_code_generator):

    def run(self, edit):
        super().base_execute(edit)

    def code_generator_settings(self):
        return "command_write"


class complete_code_generator(base_code_generator):

    def run(self, edit):
        super().base_execute(edit)

    def code_generator_settings(self):
        return "command_completions"


class whiten_code_generator(base_code_generator):

    def run(self, edit):
        super().base_execute(edit)

    def code_generator_settings(self):
        return "command_whiten"


class edit_code_generator(base_code_generator):

    def input(self, args):
        return instruction_input_handler()

    def run(self, edit, instruction):
        self.instruction = instruction
        super().base_execute(edit)

    def additional_instruction(self):
        return "Instruction: " + self.instruction

    def code_generator_settings(self):
        return "command_edits"
