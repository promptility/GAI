"""
Compatibility shim for the ``sublime_plugin`` module.

Just like ``GAI.sublime`` above, this file re‑exports the top‑level
``sublime_plugin`` module (which is a mock in the test environment) so that
``GAI.sublime_plugin`` resolves to the same object.
"""
import importlib

_sublime_plugin = importlib.import_module('sublime_plugin')
globals().update(_sublime_plugin.__dict__)
