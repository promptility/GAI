import sublime
import sublime_plugin

import json
import http.client
import threading

from abc import abstractmethod


class code_generator(sublime_plugin.TextCommand):
    def validate_setup(self):
        configurations = sublime.load_settings('gai.sublime-settings')
        api_key = configurations.get('open_ai_key', None)
        if api_key is None:
            message = "Open Ai API key missing."
            sublime.status_message(message)
            raise ValueError(message)

        if len(self.view.sel()) > 1:
            message = "Please highlight only one code segment."
            sublime.status_message(message)
            raise ValueError(message)

        selected_region = self.view.sel()[0]
        if selected_region.empty():
            message = "No section of text highlighted."
            sublime.status_message(message)
            raise ValueError(message)

    def manage_thread(self, thread, seconds=0):
        configurations = sublime.load_settings('gai.sublime-settings')
        max_time = configurations.get('max_seconds', 60)

        if seconds > max_time:
            message = "Ran out of time! {}s".format(max_time)
            sublime.status_message(message)
            return

        if thread.running:
            message = "Thinking, one moment... ({}/{}s)".format(
                seconds, max_time)
            sublime.status_message(message)
            # Wait a second, then check on it again
            sublime.set_timeout(lambda:
                                self.manage_thread(thread, seconds + 1), 1000)
            return

        if not thread.result:
            sublime.status_message(
                "Something is wrong, did not receive response - aborting")
            return

        self.view.run_command('replace_text', {
            "region": [thread.region.begin(), thread.region.end()],
            "text": thread.preCode + thread.result
        })


class base_code_generator(code_generator):

    def base_execute(self, edit):
        self.validate_setup()

        selected_region = self.view.sel()[0]
        configurations = sublime.load_settings('gai.sublime-settings')
        configurationsc = configurations.get(self.code_generator_settings())

        code_region = self.view.substr(selected_region)
        code_prompt = configurationsc.get('prompt', "")
        code_instruction = self.additional_instruction()
        user_code_content = "{} {} {}".format(
            code_prompt, code_instruction, code_region)
        data = {
            'messages': [{
                'role': 'system',
                'content': configurationsc.get('persona', 'You are a helpful assistant.')
            }, {
                'role': 'user',
                'content': user_code_content
            }],
            'model': configurationsc.get('model', "text-davinci-003"),
            'max_tokens': configurationsc.get('max_tokens', 100),
            'temperature': configurationsc.get('temperature', 0),
            'top_p': configurationsc.get('top_p', 1)
        }
        hasPreCode = configurationsc.get('keep_prompt_text')
        print(configurations.get('open_ai_endpoint'))

        if hasPreCode:
            preCode = self.view.substr(selected_region)
        else:
            preCode = ""
        thread = async_code_generator(selected_region, configurations.get(
            'open_ai_endpoint'), data, preCode)

        thread.start()
        self.manage_thread(thread)

    @abstractmethod
    def code_generator_settings(self):
        pass

    @abstractmethod
    def additional_instruction(self):
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

    def __init__(self, region, endpoint, data, preCode):
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
        self.endpoint = endpoint
        self.data = data
        self.prompt = data.get('prompt', "")
        self.preCode = preCode

    def run(self):
        self.running = True
        self.result = self.get_code_generator_response()
        self.running = False

    def get_code_generator_response(self):
        configurations = sublime.load_settings('gai.sublime-settings')

        connection = http.client.HTTPSConnection(
            configurations.get('open_ai_base'))

        headers = {
            'api-key': configurations.get('open_ai_key'),
            'Content-Type': 'application/json'
        }
        data = json.dumps(self.data)

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
