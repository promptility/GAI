# -*- coding: utf-8 -*-
"""
Package entry point for the GAI Sublime‑Text plugin.
All symbols that were previously defined in the single GAI.py file are
re‑exported here so that external code (including the test‑suite) can still
`import GAI` and access the same classes.
"""

# logger is created in async_worker.py; we import it so that callers can
# use GAI.logger if they want.
from .async_worker import logger

# Core generation machinery
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
from .config import configurator

# Commands that are invoked directly by Sublime
from .commands import replace_text_command, edit_gai_plugin_settings_command

# Small helper used by the edit command
from .instruction import instruction_input_handler

__all__ = [
    "logger",
    "code_generator",
    "base_code_generator",
    "generate_code_generator",
    "write_code_generator",
    "complete_code_generator",
    "whiten_code_generator",
    "edit_code_generator",
    "configurator",
    "replace_text_command",
    "edit_gai_plugin_settings_command",
    "instruction_input_handler",
]
