"""Unit tests for main module functionality."""

import unittest
from unittest.mock import patch, MagicMock

from src.utils.config import load_config
from src.main import HydraRemoteGUI

class TestMainSmoke(unittest.TestCase):
    """Basic smoke tests for main functionality."""

    def test_load_config_returns_dict(self):
        """Test that load_config returns a dict."""
        cfg = load_config()
        self.assertIsInstance(cfg, dict)

    @patch('src.utils.config.yaml.safe_load')
    def test_load_config_handles_missing_file(self, mock_safe_load):
        """Test load_config with missing file."""
        mock_safe_load.side_effect = FileNotFoundError()
        config = load_config("/nonexistent/path")
        self.assertEqual(config, {})

    @patch('src.utils.config.yaml.safe_load')
    def test_load_config_handles_invalid_yaml(self, mock_safe_load):
        """Test load_config with invalid YAML."""
        mock_safe_load.side_effect = Exception("Invalid YAML")
        config = load_config("/invalid/yaml")
        self.assertEqual(config, {})

    @patch('src.main.ThemedTk')
    def test_gui_initialization(self, mock_themed_tk):
        """Test that GUI initializes without errors."""
        gui = HydraRemoteGUI()
        mock_themed_tk.assert_called_once()

if __name__ == "__main__":
    unittest.main()
