import pytest
from unittest.mock import Mock
import sys

# --- Mock 'sublime' and 'sublime_plugin' modules before importing GAI ---
sys.modules['sublime'] = Mock(
    load_settings=Mock(),
    status_message=Mock(),
    active_window=Mock(),
    Region=Mock(return_value=Mock())
)
sys.modules['sublime_plugin'] = Mock()

# Import from the GAI directory structure
import GAI.core


class MockSettings:
    """Mock for sublime.Settings object"""

    def __init__(self, data):
        self.data = data

    def get(self, key, default=None):
        return self.data.get(key, default)


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


@pytest.fixture
def setup_base_generator(mock_view, mock_region):
    mock_view.sel.return_value = [mock_region]
    return mock_view, mock_region


class TestCodeGenerator:

    def test_validate_setup_single_selection(self, mock_view):
        """Test validate_setup allows single non-empty selection"""
        cmd = GAI.core.code_generator(mock_view)
        cmd.view = mock_view
        try:
            cmd.validate_setup()
        except ValueError:
            pytest.fail("validate_setup raised ValueError unexpectedly")

    def test_validate_setup_multiple_selections(self, mock_view):
        """validate_setup must raise when more than one region is selected"""
        mock_view.sel.return_value = [Mock(), Mock()]
        cmd = GAI.core.code_generator(mock_view)
        cmd.view = mock_view
        with pytest.raises(ValueError):
            cmd.validate_setup()

    def test_validate_setup_empty_selection(self, mock_view):
        """validate_setup must raise when the sole selection is empty"""
        mock_view.sel.return_value = [Mock(empty=lambda: True)]
        cmd = GAI.core.code_generator(mock_view)
        cmd.view = mock_view
        with pytest.raises(ValueError):
            cmd.validate_setup()
