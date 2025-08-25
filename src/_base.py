import sublime_plugin

def _base_text_command():
    """
    Return a suitable base class for TextCommand‑like classes.
    In the real Sublime environment ``sublime_plugin.TextCommand`` is a real
    class; in the unit‑test harness it is replaced by a ``Mock``.  Subclassing
    a mock would hide the implementation, so we fall back to ``object`` when
    the imported attribute is not a class.
    """
    return (
        sublime_plugin.TextCommand
        if isinstance(sublime_plugin.TextCommand, type)
        else object
    )
