"""
Compatibility shim for the standard‑library ``http`` package.

The tests patch ``GAI.http.client.HTTPSConnection``.  By re‑exporting the
real ``http`` package under the ``GAI.http`` name, the patch resolves to the
same object that the standard library provides.
"""
import importlib

_http = importlib.import_module('http')
globals().update(_http.__dict__)
