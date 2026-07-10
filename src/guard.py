# -*- coding: utf-8 -*-
"""Stable facade for Yadro Guard CLI."""
from src import guard_impl as _impl
_original_classify = _impl.classify
def _classify_with_types(error):
    if error.__class__.__name__ == "TypeCheckError":
        return _impl.EXIT_SOURCE
    return _original_classify(error)
_impl.classify = _classify_with_types
from src.guard_impl import *  # noqa: F401,F403,E402
