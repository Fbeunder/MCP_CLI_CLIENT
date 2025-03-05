import unittest
from unittest.mock import patch, MagicMock, mock_open, call
import json
import queue
import io
import os
import threading
from src.mcp_client import MCPClient, log, check_config, ConfigurationError, ConnectionError, CommunicationError

class TestMCPClient(unittest.TestCase):
    """Test cases voor de MCPClient class."""
    
    def setUp(self):
        """Set up voor elke test."""
        # Patch de global variabelen die normaal uit .env geladen worden
        self.patcher1 = patch('src.mcp_client.MCP_SERVER_URL', 'http://test.server/sse')
        self.patcher2 = patch('src.mcp_client.MCP_LOCAL_COMMAND', 'test_command')
        self.patcher3 = patch('src.mcp_client.API_KEY', 'test_api_key')
        self.mock_server_url = self.patcher1.start()
        self.mock_local_command = self.patcher2.start()
        self.mock_api_key = self.patcher3.start()
        
        # Patch check_config om altijd True terug te geven
        self.patcher4 = patch('src.mcp_client.check_config', return_value=True)
        self.mock_check_config = self.patcher4.start()
        
        self.client = MCPClient()
    
    def tearDown(self):
        """Tear down na elke test."""
        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()
        self.patcher4.stop()
        
    def test_initialization(self):
        """Test of de client correct initialiseert."""
        self.assertIsNone(self.client.connection)
        self.assertIsNone(self.client.transport)
        self.assertEqual(self.client._id_counter, 1)
        self.assertIsInstance(self.client._response_queue, queue.Queue)
        
    @patch('src.mcp_client.log')
    def test_check_config_success(self, mock_log):
        """Test de configuratiecontrole bij succes."""
        with patch('src.mcp_client.env_loaded', True):
            result = check_config()
            self.assertTrue(result)
            mock_log.assert_not_called()
            
    @patch('src.mcp_client.log')
    def test_check_config_failure(self, mock_log):
        """Test de configuratiecontrole bij falen."""
        with patch('src.mcp_client.env_loaded', False):
            result = check_config()
            self.assertFalse(result)
            mock_log.assert_called_once()
            
    def test_log_function_above_level(self):
        """Test de log functie met een niveau boven het ingestelde niveau."""
        with patch('src.mcp_client.current_log_level', 20):  # INFO niveau
            with patch('builtins.print') as mock_print:
                log("ERROR", "Test error")
                mock_print.assert_called_once_with("[ERROR] Test error")
                
    def test_log_function_below_level(self):
        """Test de log functie met een niveau onder het ingestelde niveau."""
        with patch('src.mcp_client.current_log_level', 20):  # INFO niveau
            with patch('builtins.print') as mock_print:
                log("DEBUG", "Test debug")
                mock_print.assert_not_called()
                
    @patch('src.mcp_client.subprocess.Popen')
    def test_connect_stdio_success(self, mock_popen):
        """Test succesvolle verbinding via STDIO."""
        # Mock het subprocess om een succesvolle verbinding te simuleren
        process_mock = MagicMock()
        process_mock.poll.return_value = None  # Proces is actief
        mock_popen.return_value = process_mock
        
        result = self.client.connect_stdio()
        
        # Controleer resultaten
        self.assertTrue(result)
        self.assertEqual(self.client.transport, "stdio")
        self.assertEqual(self.client.connection, process_mock)
        mock_popen.assert_called_once_with(
            ['test_command'], 
            stdin=unittest.mock.ANY, 
            stdout=unittest.mock.ANY, 
            stderr=unittest.mock.ANY, 
            text=True, 
            bufsize=1
        )
        
    def test_connect_stdio_failure_no_command(self):
        """Test verbindingsfout via STDIO bij ontbrekend commando."""
        # Patch de global variabele om een leeg commando te simuleren
        with patch('src.mcp_client.MCP_LOCAL_COMMAND', ''):
            result = self.client.connect_stdio('')
            
            # Controleer resultaten
            self.assertFalse(result)
            self.assertIsNone(self.client.transport)
            self.assertIsNone(self.client.connection)
    
    @patch('src.mcp_client.subprocess.Popen')
    def test_connect_stdio_process_failure(self, mock_popen):
        """Test verbindingsfout via STDIO als het proces faalt."""
        # Mock het subprocess om een gefaald proces te simuleren
        process_mock = MagicMock()
        process_mock.poll.return_value = 1  # Proces is gestopt met een foutcode
        process_mock.stderr.read.return_value = "Test error output"
        mock_popen.return_value = process_mock
        
        result = self.client.connect_stdio()
        
        # Controleer resultaten
        self.assertFalse(result)
        self.assertIsNone(self.client.transport)
    
    @patch('src.mcp_client.requests.get')
    def test_connect_sse_success(self, mock_get):
        """Test succesvolle verbinding via SSE."""
        # Mock de requests.get functie voor een succesvolle verbinding
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.client.connect_sse()
        
        # Controleer resultaten
        self.assertTrue(result)
        self.assertEqual(self.client.transport, "sse")
        mock_get.assert_called_once_with(
            'http://test.server/sse', 
            headers={'Authorization': 'Bearer test_api_key'}, 
            stream=True, 
            timeout=5
        )
        
    def test_connect_sse_failure_no_url(self):
        """Test verbindingsfout via SSE bij ontbrekende URL."""
        # Test met een lege URL
        with patch('src.mcp_client.MCP_SERVER_URL', ''):
            result = self.client.connect_sse('')
            
            # Controleer resultaten
            self.assertFalse(result)
            self.assertIsNone(self.client.transport)

    def test_connect_sse_failure_invalid_url(self):
        """Test verbindingsfout via SSE bij ongeldige URL."""
        # Test met een ongeldige URL (zonder http/https)
        result = self.client.connect_sse("invalid.url")
        
        # Controleer resultaten
        self.assertFalse(result)
        self.assertIsNone(self.client.transport)

    @patch('src.mcp_client.requests.get')
    def test_connect_sse_request_exception(self, mock_get):
        """Test verbindingsfout via SSE bij request exception."""
        # Mock de requests.get functie om een exception te werpen
        mock_get.side_effect = Exception("Test exception")
        
        result = self.client.connect_sse()
        
        # Controleer resultaten
        self.assertFalse(result)
        self.assertIsNone(self.client.transport)

    def test_send_request_no_connection(self):
        """Test het versturen van een verzoek zonder verbinding."""
        response = self.client.send_request("test_method")
        
        # Controleer resultaten
        self.assertIn("error", response)
        self.assertIsNone(self.client.transport)
        
    @patch('src.mcp_client.log')
    def test_close_no_connection(self, mock_log):
        """Test het sluiten van de client zonder verbinding."""
        self.client.close()
        
        # Controleer resultaten
        self.assertIsNone(self.client.transport)
        self.assertIsNone(self.client.connection)
        
    @patch('src.mcp_client.log')
    def test_close_stdio_connection(self, mock_log):
        """Test het sluiten van een STDIO verbinding."""
        # Simuleer een actieve STDIO verbinding
        self.client.transport = "stdio"
        mock_process = MagicMock()
        self.client.connection = mock_process
        
        self.client.close()
        
        # Controleer resultaten
        self.assertIsNone(self.client.transport)
        self.assertIsNone(self.client.connection)
        mock_process.terminate.assert_called_once()
        
    @patch('src.mcp_client.log')
    def test_close_sse_connection(self, mock_log):
        """Test het sluiten van een SSE verbinding."""
        # Simuleer een actieve SSE verbinding
        self.client.transport = "sse"
        
        self.client.close()
        
        # Controleer resultaten
        self.assertIsNone(self.client.transport)
        self.assertIsNone(self.client.connection)

if __name__ == '__main__':
    unittest.main()
