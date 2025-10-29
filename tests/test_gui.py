"""Unit tests for UI functionality."""

import unittest
from unittest.mock import MagicMock, patch
from src.main import HydraRemoteGUI

class TestGUI(unittest.TestCase):
    """Test GUI initialization and basic functionality."""
    
    @patch('src.main.ThemedTk')
    def test_gui_init(self, mock_themed_tk):
        """Test GUI initialization with default config."""
        gui = HydraRemoteGUI()
        
        # Check window was created
        mock_themed_tk.assert_called_once()
        
        # Check window title was set
        gui.window.title.assert_called_once()
        
        # Check geometry was set
        gui.window.geometry.assert_called_once()
        
    @patch('src.main.ThemedTk')
    @patch('src.main.load_config')
    def test_gui_custom_config(self, mock_load_config, mock_themed_tk):
        """Test GUI initialization with custom config."""
        # Mock custom config
        mock_load_config.return_value = {
            "ui": {
                "theme": "custom_theme",
                "window": {
                    "title": "Custom Title",
                    "width": 1000,
                    "height": 800
                }
            }
        }
        
        gui = HydraRemoteGUI()
        
        # Check custom theme was used
        mock_themed_tk.assert_called_once_with(theme="custom_theme")
        
        # Check custom title was set
        gui.window.title.assert_called_once_with("Custom Title")
        
        # Check custom geometry was set
        gui.window.geometry.assert_called_once_with("1000x800")

if __name__ == '__main__':
    unittest.main()