import unittest
from unittest.mock import patch, MagicMock, call
import sys
import io
import json
from pathlib import Path
from src.mcp_cli import main, print_env_help

class TestMCPCLI(unittest.TestCase):
    """Test cases voor de MCP CLI interface."""
    
    def setUp(self):
        """Set up voor elke test."""
        # Patch verschillende onderdelen die van de omgeving afhankelijk zijn
        self.env_patcher = patch('pathlib.Path.exists')
        self.mock_env_exists = self.env_patcher.start()
        self.mock_env_exists.return_value = True  # .env bestaat standaard
    
    def tearDown(self):
        """Tear down na elke test."""
        self.env_patcher.stop()
    
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
    @patch('src.mcp_cli.log')
    def test_no_connection_mode(self, mock_log, mock_exit):
        """Test de fout bij het niet specificeren van een verbindingsmodus."""
        main()
        mock_exit.assert_called_once_with(1)
        mock_log.assert_any_call("ERROR", "Specificeer verbindingsmodus: --local of --remote")
    
    @patch('sys.argv', ['mcp_cli.py', '--local', '--remote'])
    @patch('sys.exit')
    @patch('src.mcp_cli.log')
    def test_both_connection_modes(self, mock_log, mock_exit):
        """Test de fout bij het specificeren van beide verbindingsmodi."""
        main()
        mock_exit.assert_called_once_with(1)
        mock_log.assert_any_call("ERROR", "Kies één verbindingsmodus: --local OF --remote")
    
    @patch('sys.argv', ['mcp_cli.py', '--local'])
    @patch('sys.exit')
    @patch('src.mcp_cli.log')
    @patch('os.getenv')
    def test_local_without_command(self, mock_getenv, mock_log, mock_exit):
        """Test lokale verbinding zonder commando in .env."""
        mock_getenv.return_value = None  # MCP_LOCAL_COMMAND is niet ingesteld
        main()
        mock_exit.assert_called_once_with(1)
        mock_log.assert_any_call("ERROR", "MCP_LOCAL_COMMAND niet ingesteld in .env bestand")
    
    @patch('sys.argv', ['mcp_cli.py', '--remote'])
    @patch('sys.exit')
    @patch('src.mcp_cli.log')
    @patch('os.getenv')
    def test_remote_without_url(self, mock_getenv, mock_log, mock_exit):
        """Test remote verbinding zonder URL in .env."""
        mock_getenv.return_value = None  # MCP_SERVER_URL is niet ingesteld
        main()
        mock_exit.assert_called_once_with(1)
        mock_log.assert_any_call("ERROR", "MCP_SERVER_URL niet ingesteld in .env bestand")
    
    @patch('sys.argv', ['mcp_cli.py', '--local', '--method', 'getVersion'])
    @patch('src.mcp_client.MCPClient')
    @patch('os.getenv')
    def test_direct_method_call(self, mock_getenv, mock_client_class):
        """Test een directe methode-aanroep via command-line argumenten."""
        # Setup mocks
        mock_getenv.return_value = "test_command"
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.connect_stdio.return_value = True
        mock_client.send_request.return_value = {"result": "1.0.0"}
        
        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            main()
            
            # Controleren van de output
            output = captured_output.getvalue()
            self.assertIn('"result": "1.0.0"', output)
            
            # Controleren van de methode-aanroepen
            mock_client.connect_stdio.assert_called_once()
            mock_client.send_request.assert_called_once_with("getVersion", None)
            mock_client.close.assert_called_once()
        finally:
            sys.stdout = sys.__stdout__  # Reset stdout
    
    @patch('sys.argv', ['mcp_cli.py', '--local', '--method', 'add', '--params', '{"a": 1, "b": 2}'])
    @patch('src.mcp_client.MCPClient')
    @patch('os.getenv')
    def test_direct_method_call_with_params(self, mock_getenv, mock_client_class):
        """Test een directe methode-aanroep met parameters via command-line argumenten."""
        # Setup mocks
        mock_getenv.return_value = "test_command"
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.connect_stdio.return_value = True
        mock_client.send_request.return_value = {"result": 3}
        
        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            main()
            
            # Controleren van de output
            output = captured_output.getvalue()
            self.assertIn('"result": 3', output)
            
            # Controleren van de methode-aanroepen
            mock_client.connect_stdio.assert_called_once()
            mock_client.send_request.assert_called_once_with("add", {"a": 1, "b": 2})
            mock_client.close.assert_called_once()
        finally:
            sys.stdout = sys.__stdout__  # Reset stdout
    
    @patch('sys.argv', ['mcp_cli.py', '--local', '--method', 'add', '--params', 'invalid-json'])
    @patch('sys.exit')
    @patch('src.mcp_cli.log')
    @patch('os.getenv')
    def test_direct_method_call_invalid_params(self, mock_getenv, mock_log, mock_exit):
        """Test een directe methode-aanroep met ongeldige JSON parameters."""
        mock_getenv.return_value = "test_command"
        main()
        mock_exit.assert_called_once_with(1)
        mock_log.assert_any_call("ERROR", "Ongeldige JSON in params: invalid-json")
    
    @patch('builtins.print')
    def test_print_env_help(self, mock_print):
        """Test de print_env_help functie."""
        print_env_help()
        # Controleer dat print meerdere keren wordt aangeroepen
        self.assertTrue(mock_print.call_count > 1)
        # Controleer dat de uitvoer informatie over het .env bestand bevat
        calls = [call for args, kwargs in mock_print.call_args_list for call in args]
        any_env_mention = any(".env" in call for call in calls if isinstance(call, str))
        self.assertTrue(any_env_mention)

if __name__ == '__main__':
    unittest.main()
