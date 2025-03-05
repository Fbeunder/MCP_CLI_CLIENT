import unittest
from unittest.mock import patch, MagicMock
import sys
import io
from src.mcp_cli import main

class TestMCPCLI(unittest.TestCase):
    """Test cases voor de MCP CLI interface."""
    
    @patch('sys.argv', ['mcp_cli.py', '--show-config'])
    @patch('sys.exit')
    @patch('builtins.print')
    def test_show_config(self, mock_print, mock_exit):
        """Test het '--show-config' argument."""
        main()
        mock_exit.assert_called_once_with(0)
        # Controleer dat er meerdere malen wordt geprint
        self.assertTrue(mock_print.call_count > 1)
    
    @patch('sys.argv', ['mcp_cli.py'])
    @patch('sys.exit')
    @patch('pathlib.Path.exists')
    @patch('src.mcp_cli.log')
    def test_no_connection_mode(self, mock_log, mock_exists, mock_exit):
        """Test de fout bij het niet specificeren van een verbindingsmodus."""
        mock_exists.return_value = True  # .env bestaat
        main()
        mock_exit.assert_called_once_with(1)
        mock_log.assert_called_with("ERROR", "Specificeer verbindingsmodus: --local of --remote")
    
    @patch('sys.argv', ['mcp_cli.py', '--local', '--remote'])
    @patch('sys.exit')
    @patch('pathlib.Path.exists')
    @patch('src.mcp_cli.log')
    def test_both_connection_modes(self, mock_log, mock_exists, mock_exit):
        """Test de fout bij het specificeren van beide verbindingsmodi."""
        mock_exists.return_value = True  # .env bestaat
        main()
        mock_exit.assert_called_once_with(1)
        mock_log.assert_called_with("ERROR", "Kies één verbindingsmodus: --local OF --remote")
        
    # Meer test cases volgen voor verschillende scenario's...

if __name__ == '__main__':
    unittest.main()
