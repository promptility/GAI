import sublime
import sublime_plugin

import json
import http.client
import threading
from time import sleep
from abc import abstractmethod


class code_generator(sublime_plugin.TextCommand):
    """
    A class used to generate code using OpenAI.

    Methods
    -------
    validate_setup():
        Validates the setup by checking the API key and the selected region of text.
    manage_thread(thread, seconds=0):
        Manages the running thread and checks if it's still running or if it has a result.
    """

    def validate_setup(self):
        """
        Validates the setup by checking the API key and the selected region of text.
        """
        # configurations = sublime.load_settings('gai.sublime-settings')
        # api_key = configurations.get('open_ai_key', None)
        # if api_key is None:
        #     message = "Open Ai API key missing."
        #     sublime.status_message(message)
        #     raise ValueError(message)

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
        Manages the running thread and checks if it's still running or if it has a result.

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


class config_handler():

    def __init__(self, configurations, section_name, base_obj):
        self.base_obj = base_obj
        self.__section_cursor__ = section_name

        # Read Sublime Text configuration object
        self.source_config = {}
        self.source_config["oai"] = configurations.get("oai", {})
        self.source_config[section_name] = configurations.get(
            "commands", {}).get(section_name, {})

        # Read the section configuration
        self.__running_config__ = {}
        self.__running_config__["alternates"] = configurations.get(
            "alternates", {})
        self.__configuration__completed__ = False
        self.__construct__running__config__()

    def __construct__running__config__(self):

        def populate_dict(input_dict, target_dict):
            def check_dict(k):
                if k in target_dict.keys() and \
                        k not in input_dict.keys() and \
                        not isinstance(target_dict[k], dict):
                    return target_dict[k]
                if isinstance(input_dict[k], dict):
                    if k not in target_dict.keys():
                        target_dict[k] = {}
                    return populate_dict(input_dict[k], target_dict[k])
                return input_dict[k]

            keys = set(list(target_dict.keys()) + list(input_dict.keys()))
            return {k: check_dict(k) if k in input_dict.keys()
                    else target_dict[k] for k in keys}

        # Construct oai configuration from global and section
        default_oai = self.source_config["oai"]
        self.__running_config__ = populate_dict(
            default_oai, self.__running_config__)

        section_config = self.source_config[self.__section_cursor__]
        self.__running_config__ = populate_dict(
            section_config, self.__running_config__)

        def replace_config(config_name):
            if config_name:
                alternates = self.__running_config__["alternates"]
                config_override = alternates[config_name]
                self.__running_config__ = populate_dict(
                    config_override, self.__running_config__)

        def on_done(index):
            if index == -1:
                self.__configuration__completed__ = True
                return
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
            self.base_obj.view.window().show_quick_panel(
                ["default"] + list(alternates.keys()), on_select=on_done)

    def ready_wait(self, timeout=10):
        timeout = 0 - timeout
        while timeout < 0 and not self.__configuration__completed__:
            sleep(1)
            print("--sleeping--")
            timeout += 1

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
        """
        Executes the code generation process.

        :param edit: The text to be edited.
        """
        self.validate_setup()
        selected_region = self.view.sel()[0]

        # Load sublime configuration into config handler
        configurations = sublime.load_settings('gai.sublime-settings')
        section_name = self.code_generator_settings()

        # This reads the configuration but may not have completed parsing the
        # config even after exiting
        config_handle = config_handler(configurations, section_name, self)

        # Read selection of text from editor
        code_region = self.view.substr(selected_region)

        def create_data():

            data_container = {"text": None, "data": None}

            def async_prepare():
                # async_prepare the request
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

            prepthread = threading.Thread(target=async_prepare)
            prepthread.start()

            def await_result(field):
                prepthread.join()
                return data_container.get(field)

            return await_result

        # Launch thread for async processing of user input and request
        data_handle = create_data()
        codex_thread = async_code_generator(selected_region, config_handle,
                                            data_handle)
        codex_thread.start()
        self.manage_thread(codex_thread, config_handle.__running_config__[
                           "max_seconds"], 60)

    @ abstractmethod
    def code_generator_settings(self):
        """
        Abstract method to be implemented by child classes. Should return the
        settings for the code generator.
        """
        pass

    @ abstractmethod
    def additional_instruction(self):
        """
        Abstract method to be implemented by child classes. Should return any
        additional instructions for the code generation.

        :return: An empty string by default.
        """
        return ""


class write_code_generator(base_code_generator):

    def run(self, edit):
        super().base_execute(edit)

    def code_generator_settings(self):
        return "write"


class complete_code_generator(base_code_generator):

    def run(self, edit):
        super().base_execute(edit)

    def code_generator_settings(self):
        return "completions"


class whiten_code_generator(base_code_generator):

    def run(self, edit):
        super().base_execute(edit)

    def code_generator_settings(self):
        return "whiten"


class edit_code_generator(base_code_generator):

    def input(self, args):
        return instruction_input_handler()

    def run(self, edit, instruction):
        self.instruction = instruction
        super().base_execute(edit)

    def additional_instruction(self):
        return "Instruction: " + self.instruction

    def code_generator_settings(self):
        return "edits"


class instruction_input_handler(sublime_plugin.TextInputHandler):
    def name(self):
        return "instruction"

    def placeholder(self):
        return "E.g.: 'translate to java' or 'add documentation'"


class async_code_generator(threading.Thread):
    running = False
    result = None

    def __init__(self, region, config_handle, data_handle):
        """
        Args:
            Key (str): The specific user's API key provided by Open-AI.

            Prompt (str): The code or text string that GPT3 will manipulate.

            Region (str): The highlighted area in sublime-text that we are
            examining and where the result will be placed.

            Instruction (str, optional): An instruction is required for the
            edit endpoint, such as "translate this code to JavaScript". If
            only code generation is needed, leave it as None.

        Returns:
            None
        """
        super().__init__()

        self.region = region
        self.config_handle = config_handle
        self.data_handle = data_handle

    def run(self):
        self.running = True
        self.result = self.get_code_generator_response()
        self.running = False

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
            'Content-Type': 'application/json'
        }
        data = json.dumps(self.data)

        print("=== Connection ===")
        print(self.endpoint)
        print("=== Data === ")
        print(self.data)
        print("=== API Key ===")
        print(headers)
        print("===============")

        connection.request('POST', self.endpoint, body=data, headers=headers)
        response = connection.getresponse()
        response_dict = json.loads(response.read().decode())

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
    """
    A Sublime Text command class that replaces a specified region of text with
    new text.

    Attributes:
        view (sublime.View): The view where the command is executed.
    """

    def run(self, edit, region, text):
        """
        The main method that is run when the command is executed.

        Args: edit (sublime.Edit): The edit token used to group changes into a
            single undo/redo operation.

            region (tuple): A tuple representing the region of text to be
            replaced.

            text (str): The new text that will replace the old text in the
            specified region.

        Returns:
            None
        """
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
