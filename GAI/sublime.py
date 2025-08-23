"""
Compatibility shim for the ``sublime`` module.

The real Sublime Text API is not available when the tests run, so the test
suite injects a mock into ``sys.modules['sublime']``.  This file exists only
so that ``import GAI.sublime`` does not raise ``ModuleNotFoundError``.
We simply re‑export the *top‑level* ``sublime`` module (which may be the
mock created by the tests) so that ``GAI.sublime`` points to the same object.
"""
import importlib

_sublime = importlib.import_module('sublime')
# Export everything the mock provides (or the real API if available)
globals().update(_sublime.__dict__)
