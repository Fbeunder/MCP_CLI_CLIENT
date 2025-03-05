import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import queue
from src.mcp_client import MCPClient, ConfigurationError, ConnectionError, CommunicationError

class TestMCPClient(unittest.TestCase):
    """Test cases voor de MCPClient class."""
    
    def setUp(self):
        """Set up voor elke test."""
        self.client = MCPClient()
        
    @patch('src.mcp_client.check_config')
    def test_initialization(self, mock_check_config):
        """Test of de client correct initialiseert."""
        mock_check_config.return_value = True
        client = MCPClient()
        self.assertIsNone(client.connection)
        self.assertIsNone(client.transport)
        self.assertEqual(client._id_counter, 1)
        self.assertIsInstance(client._response_queue, queue.Queue)
        
    @patch('src.mcp_client.subprocess.Popen')
    @patch('src.mcp_client.MCP_LOCAL_COMMAND', 'test_command')
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
        
    @patch('src.mcp_client.subprocess.Popen')
    def test_connect_stdio_failure_no_command(self, mock_popen):
        """Test verbindingsfout via STDIO bij ontbrekend commando."""
        # Test met een leeg commando
        result = self.client.connect_stdio("")
        
        # Controleer resultaten
        self.assertFalse(result)
        self.assertIsNone(self.client.transport)
        self.assertIsNone(self.client.connection)
        mock_popen.assert_not_called()  # Popen mag niet aangeroepen worden
    
    @patch('src.mcp_client.requests.get')
    @patch('src.mcp_client.MCP_SERVER_URL', 'http://test.server/sse')
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
        
    @patch('src.mcp_client.requests.get')
    def test_connect_sse_failure_no_url(self, mock_get):
        """Test verbindingsfout via SSE bij ontbrekende URL."""
        # Test met een lege URL
        result = self.client.connect_sse("")
        
        # Controleer resultaten
        self.assertFalse(result)
        self.assertIsNone(self.client.transport)
        mock_get.assert_not_called()  # requests.get mag niet aangeroepen worden

    @patch('src.mcp_client.requests.get')
    def test_connect_sse_failure_invalid_url(self, mock_get):
        """Test verbindingsfout via SSE bij ongeldige URL."""
        # Test met een ongeldige URL (zonder http/https)
        result = self.client.connect_sse("invalid.url")
        
        # Controleer resultaten
        self.assertFalse(result)
        self.assertIsNone(self.client.transport)
        mock_get.assert_not_called()  # requests.get mag niet aangeroepen worden

    # Tests voor send_request en andere methoden volgen...

if __name__ == '__main__':
    unittest.main()
