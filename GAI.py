import sublime
import sublime_plugin
import os
import json
import http.client
import threading
from time import sleep
from abc import abstractmethod
import logging

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a formatter and attach it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class code_generator(sublime_plugin.TextCommand):
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
        Manages the running thread and checks if it's still running or if it
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


class configurator():

    def __init__(self, configurations, section_name, base_obj):
        self.base_obj = base_obj
        self.__section_cursor__ = section_name

        self.cancelled = False  

        self.source_config__meta__ = configurations.get("__meta__", {})

        # Read Sublime Text configuration object
        self.source_config = {}
        self.source_config["oai"] = configurations.get("oai", {})
        self.source_config[section_name] = configurations.get(section_name, {})

        # Read the section configuration
        self.__running_config__ = {}
        self.__running_config__["alternates"] = configurations.get(
            "alternates", {})
        self.__configuration__completed__ = False
        self.__construct__running__config__()

    def __construct__running__config__(self):

        def populate_dict(input_dict, target_dict):

            def merge_value(input_val, target_val, key):
                # Determine which priority lists apply for the current key
                target_prio_str_keys = self.source_config__meta__.get(
                    "target_prio_str_keys", [])
                input_prio_str_keys = self.source_config__meta__.get(
                    "input_prio_str_keys", [])
                input_prio_keys = self.source_config__meta__.get(
                    "input_prio_keys", [])

                if key in target_prio_str_keys:
                    # Target (global) value first, then input (more specific)
                    return target_val + "\n\n" + input_val
                elif key in input_prio_str_keys:
                    # Input (more specific) value first, then target
                    return input_val + "\n\n" + target_val
                elif key in input_prio_keys:
                    # Input overrides target completely
                    return input_val
                else:
                    # Default: keep target value
                    return target_val

            def merge_dict_value(lhs, rhs, k):
                # Merge a dict with a scalar value (or vice‑versa)
                if isinstance(lhs, dict):
                    dict_val = lhs
                    val = rhs
                else:
                    dict_val = rhs
                    val = lhs

                merged = dict(dict_val)  # copy to avoid mutating original
                merged[k] = val
                return merged

            def merge_dict(k):
                # Return value if key only exists in one of the dicts
                if k in target_dict and k not in input_dict:
                    return target_dict[k]
                if k in input_dict and k not in target_dict:
                    return input_dict[k]

                # Both dicts contain the key
                if k in input_dict and k in target_dict:
                    # Both values are non‑dicts → apply string/priority merge
                    if not isinstance(input_dict[k], dict) and not isinstance(target_dict[k], dict):
                        return merge_value(input_dict[k], target_dict[k], k)

                    # Both values are dicts → recurse
                    if isinstance(input_dict[k], dict) and isinstance(target_dict[k], dict):
                        return populate_dict(input_dict[k], target_dict[k])

                    # One dict, one scalar → merge appropriately
                    return merge_dict_value(input_dict[k], target_dict[k], k)

                # Fallback (should not happen)
                return None

            keys = set(list(target_dict.keys()) + list(input_dict.keys()))
            return {k: merge_dict(k) for k in keys}

        # Construct oai configuration from global and section
        default_oai = self.source_config["oai"]
        self.__running_config__ = populate_dict(
            default_oai, self.__running_config__)

        # Merge the specific command section
        section_config = self.source_config[self.__section_cursor__]
        self.__running_config__ = populate_dict(
            section_config, self.__running_config__)

        def replace_config(config_name):
            if config_name:
                alternates = self.__running_config__["alternates"]
                config_override = alternates[config_name]
                self.__running_config__ = populate_dict(
                    self.__running_config__, config_override)

        def on_done(index):
            if index == -1:
                self.cancelled = True  
            else:
                configs_list = ["__default__"]
                configs_list += list(alternates.keys())
                selected_config = configs_list[index]
                if selected_config != "__default__":
                    replace_config(selected_config)
            self.__configuration__completed__ = True

        default_alternate = self.__running_config__[
            "alternates"].get("default", None)
        if default_alternate is not None:
            replace_config(default_alternate)
            self.__configuration__completed__ = True
        else:
            alternates = self.__running_config__["alternates"]
            # Show quick panel for user selection
            self.base_obj.view.window().show_quick_panel(
                ["default"] + list(alternates.keys()), on_select=on_done)

    def ready_wait(self, sleep_duration=0.2):
        while not self.__configuration__completed__:
            sleep(sleep_duration)

    def is_cancelled(self):
        self.ready_wait()
        return self.cancelled

    def get_prompt(self, default=""):
        self.ready_wait()
        return self.__running_config__.get("prompt", default)

    def get_persona(self, default="You are a helpful AI Assistant"):
        self.ready_wait()
        return self.__running_config__.get("persona", default)

    def get_model(self, default="gpt-4"):
        self.ready_wait()
        return self.__running_config__.get("model", default)

    def get(self, key, default=None):
        self.ready_wait()
        return self.__running_config__.get(key, default)


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


class instruction_input_handler(sublime_plugin.TextInputHandler):
    def name(self):
        return "instruction"

    def placeholder(self):
        return "E.g.: 'translate to java' or 'add documentation'"


class async_code_generator(threading.Thread):
    running = False
    result = None

    def __init__(self, region, config_handle, data_handle):
        super().__init__()

        self.region = region
        self.config_handle = config_handle
        self.data_handle = data_handle

        self.logging_file_handler = None

    def run(self):
        self.running = True
        self.setup_logs()
        if not self.config_handle.is_cancelled():
            self.result = self.get_code_generator_response()
        else:
            self.result = []

        if self.logging_file_handler is not None:
            self.logging_file_handler.close()
            logger.removeHandler(self.logging_file_handler)
        
        self.running = False

    def setup_logs(self):

        def stream_handler_added():
            return any(isinstance(handler, logging.StreamHandler) 
                for handler in logger.handlers)

        def same(cur_handler, lfile):
            cur_file = os.path.abspath(cur_handler.baseFilename)
            return cur_file == os.path.abspath(lfile)

        def file_handler_added(logfile):
            return any(isinstance(handler, logging.FileHandler) 
                and same(handler, logfile) for handler in logger.handlers)

        # Add a stream handler if not already defined given configuration
        if self.config_handle.get("log_level", None) is not None:
            if not stream_handler_added():
                stream_handler = logging.StreamHandler()
                stream_handler.setFormatter(formatter)
                logger.addHandler(stream_handler)

        # Add a file handler if not already present given configuration
        file_log_io = self.config_handle.get("log_file", None)
        
        if file_log_io is not None and not file_handler_added(file_log_io):
            file_handler = logging.FileHandler(file_log_io)
            self.logging_file_handler = file_handler
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    def get_code_generator_response(self):

        self.endpoint = self.config_handle.get("open_ai_endpoint")
        self.apibase = self.config_handle.get("open_ai_base")
        self.apikey = self.config_handle.get("open_ai_key")
        self.data = self.data_handle("data")
        self.text_replace = self.data_handle("text")

        connection = http.client.HTTPSConnection(
            self.apibase)

        headers = {
            'api-key': self.apikey,
            'Authorization': 'Bearer {}'.format(self.apikey),
            'Content-Type': 'application/json'
        }
        data = json.dumps(self.data)


        log_level = self.config_handle.get("log_level", None)

        # print("Configuration before execution of request \n\n")
        # print(self.config_handle.__running_config__)

        if log_level in ["requests", "all"]:
            logger.info("Request Headers: %s", json.dumps(headers, indent=4))
            logger.info("Request Data: %s", json.dumps(self.data, indent=4))

        connection.request('POST', self.endpoint, body=data, headers=headers)
        response = connection.getresponse()

        if log_level in ["all"]:
            logger.info("Response Status: %s", response.status)
            logger.info("Response Headers: %s", json.dumps(dict(response.headers), indent=4))

        response_dict = json.loads(response.read().decode())

        if log_level in ["all"]:
            logger.info("Response Data: %s", json.dumps(response_dict, indent=4))

        if response_dict.get('error', None):
            raise ValueError(response_dict['error'])
        else:
            choice = response_dict.get('choices', [{}])[0]
            ai_code = choice['message']['content']
            usage = response_dict['usage']['total_tokens']
            sublime.status_message("Tokens used: " + str(usage))
        return ai_code

    def get_max_seconds(self):
        return self.config_handle.get("max_seconds", 60)


class replace_text_command(sublime_plugin.TextCommand):

    def run(self, edit, region, text):
        region = sublime.Region(*region)
        self.view.replace(edit, region, text)


class edit_gai_plugin_settings_command(sublime_plugin.ApplicationCommand):
    def run(self):

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
