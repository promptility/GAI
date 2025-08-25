# -*- coding: utf-8 -*-
"""
Package façade for the GAI Sublime‑Text plugin.
All symbols that were previously defined in the single GAI.py file are
re‑exported here so that external code (including the test‑suite) can still
`import GAI` and access the same classes.
"""

# Import the *top-level* modules (they are patched by the test suite).
import importlib
import sys

_sublime = importlib.import_module('sublime')
_sublime_plugin = importlib.import_module('sublime_plugin')
_http = importlib.import_module('http')

# Re‑export them under the expected names.
sublime = _sublime
sublime_plugin = _sublime_plugin
http = _http

# Register the submodule names so that ``patch('GAI.sublime…')`` and
# ``patch('GAI.http.client…')`` resolve to the same objects that the tests
# have mocked.
sys.modules[__name__ + '.sublime'] = _sublime
sys.modules[__name__ + '.sublime_plugin'] = _sublime_plugin
sys.modules[__name__ + '.http'] = _http

# Core generation machinery
from .async_worker import async_code_generator, logger
from .core import (
    code_generator,
    base_code_generator,
    generate_code_generator,
    write_code_generator,
    complete_code_generator,
    whiten_code_generator,
    edit_code_generator,
)

# Config handling
from .config import gai_config

# Commands that are invoked directly by Sublime
from .commands import replace_text_command, edit_gai_plugin_settings_command, generate_text_command

# Small helper used by the edit command
from .instruction import instruction_input_handler

__all__ = [
    "sublime",
    "sublime_plugin",
    "http",
    "logger",
    "code_generator",
    "base_code_generator",
    "generate_code_generator",
    "write_code_generator",
    "complete_code_generator",
    "whiten_code_generator",
    "edit_code_generator",
    "gai_config",
    "replace_text_command",
    "edit_gai_plugin_settings_command",
    "generate_text_command",
    "instruction_input_handler",
    "async_code_generator",
]
