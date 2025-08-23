import pytest
from unittest.mock import Mock
import sys

# --- Mock 'sublime' and 'sublime_plugin' modules ---
sys.modules['sublime'] = Mock(
    load_settings=Mock(),
    status_message=Mock(),
    active_window=Mock(),
    Region=Mock(return_value=Mock())
)
sys.modules['sublime_plugin'] = Mock()


@pytest.fixture
def mock_view():
    view = Mock()
    view.sel.return_value = [Mock(empty=lambda: False, begin=lambda: 0, end=lambda: 10)]
    view.substr.return_value = "print('hello')"
    view.replace = Mock()
    return view


@pytest.fixture
def mock_region():
    region = Mock()
    region.empty.return_value = False
    region.begin.return_value = 10
    region.end.return_value = 20
    return region


class MockSettings:
    """Mock for sublime.Settings object"""

    def __init__(self, data):
        self.data = data

    def get(self, key, default=None):
        return self.data.get(key, default)
