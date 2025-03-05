import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import os
import io
import sys
import tempfile
from pathlib import Path
from src.mcp_client import MCPClient
import src.mcp_cli as mcp_cli

class TestIntegration(unittest.TestCase):
    """Integratietests voor de MCP client.
    
    Deze tests controleren of verschillende delen van de applicatie correct samenwerken.
    In werkelijkheid zouden deze tests kunnen worden uitgevoerd met een mock MCP server,
    maar voor nu gebruiken we patches om externe afhankelijkheden te mocken.
    """
    
    def setUp(self):
        """Set up voor elke test."""
        # Patch common dependencies
        self.patcher1 = patch('src.mcp_client.MCP_SERVER_URL', 'http://test.server/sse')
        self.patcher2 = patch('src.mcp_client.MCP_LOCAL_COMMAND', 'test_command')
        self.patcher3 = patch('src.mcp_client.API_KEY', 'test_api_key')
        self.patcher4 = patch('src.mcp_client.check_config', return_value=True)
        
        self.mock_server_url = self.patcher1.start()
        self.mock_local_command = self.patcher2.start()
        self.mock_api_key = self.patcher3.start()
        self.mock_check_config = self.patcher4.start()
        
    def tearDown(self):
        """Tear down na elke test."""
        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()
        self.patcher4.stop()
    
    @patch('src.mcp_client.subprocess.Popen')
    def test_send_request_via_stdio(self, mock_popen):
        """Test het versturen van een verzoek via STDIO."""
        # Mock het subprocess
        process_mock = MagicMock()
        process_mock.poll.return_value = None  # Proces is actief
        
        # Simuleer een antwoord van het subprocess
        expected_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "1.0.0"
        }
        
        # Mock het stdout attribuut van het proces om een respons terug te geven
        process_mock.stdout = MagicMock()
        process_mock.stdout.__iter__.return_value = [json.dumps(expected_response)]
        
        mock_popen.return_value = process_mock
        
        # Maak een client en verstuur het verzoek
        client = MCPClient()
        result = client.connect_stdio()
        self.assertTrue(result)
        
        response = client.send_request("getVersion")
        
        # Controleer resultaten
        self.assertEqual(response, expected_response)
        
        # Controleer dat stdin.write is aangeroepen met het juiste verzoek
        expected_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getVersion"
        }
        process_mock.stdin.write.assert_called_once_with(json.dumps(expected_request) + "\n")
        process_mock.stdin.flush.assert_called_once()
        
    @patch('src.mcp_client.requests.get')
    @patch('src.mcp_client.requests.post')
    def test_send_request_via_sse(self, mock_post, mock_get):
        """Test het versturen van een verzoek via SSE."""
        # Mock de requests.get functie voor een succesvolle verbinding
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Mock de requests.post functie voor een succesvolle POST
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post.return_value = mock_post_response
        
        # Simuleer een antwoord via de response queue
        expected_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "1.0.0"
        }
        
        client = MCPClient()
        
        # Injecteer de verwachte respons in de response queue
        client._response_queue.put(expected_response)
        
        # Verbind en verstuur het verzoek
        result = client.connect_sse()
        self.assertTrue(result)
        
        response = client.send_request("getVersion")
        
        # Controleer resultaten
        self.assertEqual(response, expected_response)
        
        # Controleer dat requests.post is aangeroepen met het juiste verzoek
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], 'http://test.server/sse')  # URL
        self.assertEqual(kwargs['headers'], {"Content-Type": "application/json", "Authorization": "Bearer test_api_key"})
        
        expected_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getVersion"
        }
        self.assertEqual(kwargs['json'], expected_request)
        
    @patch('sys.argv', ['mcp_cli.py', '--local', '--method', 'getVersion'])
    @patch('src.mcp_client.subprocess.Popen')
    @patch('os.getenv')
    @patch('pathlib.Path.exists')
    def test_cli_to_client_integration(self, mock_exists, mock_getenv, mock_popen):
        """Test de integratie tussen CLI en Client modules."""
        # Setup mocks
        mock_exists.return_value = True  # .env bestaat
        mock_getenv.return_value = "test_command"
        
        # Mock het subprocess
        process_mock = MagicMock()
        process_mock.poll.return_value = None  # Proces is actief
        
        # Simuleer een antwoord van het subprocess
        expected_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "1.0.0"
        }
        
        # Mock het stdout attribuut van het proces om een respons terug te geven
        process_mock.stdout = MagicMock()
        process_mock.stdout.__iter__.return_value = [json.dumps(expected_response)]
        
        mock_popen.return_value = process_mock
        
        # Redirect stdout voor testing
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            # Voer CLI main functie uit
            mcp_cli.main()
            
            # Controleer resultaten
            output = captured_output.getvalue()
            self.assertIn('"result": "1.0.0"', output)
        finally:
            sys.stdout = sys.__stdout__  # Reset stdout

if __name__ == '__main__':
    unittest.main()
