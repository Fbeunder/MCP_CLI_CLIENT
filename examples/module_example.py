#!/usr/bin/env python
"""
MCP CLI Client Module Usage Example

Dit script demonstreert hoe de MCP CLI Client te gebruiken als een Python module
in een ander Python project. Het toont zowel lokale als remote verbindingen
en het versturen van JSON-RPC verzoeken.
"""

import os
import json
from dotenv import load_dotenv
from mcp_cli_client import MCPClient, log

def main():
    """
    Demonstreert het gebruik van de MCP CLI Client als Python module.
    """
    # Laad configuratie uit .env bestand
    load_dotenv()
    
    # Maak een nieuwe MCPClient instantie
    client = MCPClient()
    
    try:
        # Voorbeeld 1: Verbind met een lokale MCP server
        local_command = os.getenv("MCP_LOCAL_COMMAND")
        if local_command:
            print(f"Verbinden met lokale MCP server: {local_command}")
            if client.connect_stdio(local_command):
                # Verstuur een getVersion verzoek
                response = client.send_request("getVersion")
                print("Resultaat van getVersion verzoek:")
                print(json.dumps(response, indent=2))
                
                # Verstuur een tweede verzoek met parameters
                response = client.send_request("echo", {"message": "Hallo van Python module!"})
                print("Resultaat van echo verzoek:")
                print(json.dumps(response, indent=2))
                
                # Sluit de verbinding
                client.close()
        
        # Voorbeeld 2: Verbind met een remote MCP server via SSE
        remote_url = os.getenv("MCP_SERVER_URL")
        if remote_url:
            print(f"Verbinden met remote MCP server: {remote_url}")
            if client.connect_sse(remote_url):
                # Verstuur een getStatus verzoek
                response = client.send_request("getStatus")
                print("Resultaat van getStatus verzoek:")
                print(json.dumps(response, indent=2))
                
                # Sluit de verbinding
                client.close()
    except Exception as e:
        print(f"Fout: {e}")
    finally:
        # Zorg dat de verbinding altijd wordt afgesloten
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    main()
