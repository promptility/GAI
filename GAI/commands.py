import sublime
import sublime_plugin
from ._base import _base_text_command

class replace_text_command(_base_text_command()):
    """
    Simple command that replaces the text in the given region.
    In the real Sublime environment the command is instantiated by the
    editor and receives the view automatically.  In the unit‑tests we
    instantiate the command manually, so we need an ``__init__`` that
    accepts the view and stores it on the instance.
    """
    def __init__(self, view):
        # ``_base_text_command`` may be ``object`` in the test harness,
        # therefore we cannot rely on ``super()`` calling a real base
        # ``__init__``.  Simply store the view for later use.
        self.view = view

    def run(self, edit, region, text):
        # ``region`` is supplied as a tuple (begin, end).  The real
        # Sublime API expects a ``sublime.Region`` instance, which is
        # mocked in the test suite.  Expanding the tuple creates the
        # mock Region object.
        region = sublime.Region(*region)
        self.view.replace(edit, region, text)


class edit_gai_plugin_settings_command(
        sublime_plugin.ApplicationCommand
        if isinstance(sublime_plugin.ApplicationCommand, type)
        else object):
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
