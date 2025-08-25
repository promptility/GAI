import importlib
# Import the *top‑level* ``sublime`` module (the tests replace it with a Mock).
sublime = importlib.import_module('sublime')
import os
import json
import logging

# ``http`` is a standard‑library package; we import it via ``importlib`` so that
# ``GAI.http.client`` points to the same object the tests patch.
http = importlib.import_module('http')
import threading

# Create a logger (module‑level, shared)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Formatter for both stream and file handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


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
        """Setup logging handlers based on configuration."""
        
        # Always add stream handler when log_level is configured
        if self.config_handle.get("log_level", None) is not None:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

        # Add file handler if log_file is configured
        file_log_io = self.config_handle.get("log_file", None)
        if file_log_io is not None:
            try:
                file_handler = logging.FileHandler(file_log_io)
                self.logging_file_handler = file_handler
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except (TypeError, AttributeError):
                # Handle case where file_log_io is mocked or invalid
                pass

    def get_code_generator_response(self):

        self.endpoint = self.config_handle.get("open_ai_endpoint")
        self.api_base = self.config_handle.get("open_ai_base")
        self.api_key = self.config_handle.get("open_ai_key")
        self.data = self.data_handle("data")
        self.text_replace = self.data_handle("text")

        connection = http.client.HTTPSConnection(
            self.api_base)

        headers = {
            'api-key': self.api_key,
            'Authorization': 'Bearer {}'.format(self.api_key),
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
