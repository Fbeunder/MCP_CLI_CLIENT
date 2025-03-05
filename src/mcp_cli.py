#!/usr/bin/env python
"""
MCP CLI - Command Line Interface voor de MCP Client

Deze module biedt een command-line interface voor het verbinden met en sturen van 
verzoeken naar MCP servers, zowel lokaal (via STDIO) als remote (via SSE).
"""

import argparse
import json
import sys
from src.mcp_client import MCPClient, log

def main():
    """Hoofdfunctie voor de MCP CLI."""
    parser = argparse.ArgumentParser(description="MCP Command Line Interface")
    
    # Verbindingsopties
    connection_group = parser.add_argument_group("Connection Options")
    connection_group.add_argument(
        "--local", "-l", action="store_true", help="Use local connection via STDIO"
    )
    connection_group.add_argument(
        "--remote", "-r", action="store_true", help="Use remote connection via SSE"
    )
    
    # Command opties
    command_group = parser.add_argument_group("Command Options")
    command_group.add_argument(
        "--method", "-m", type=str, help="JSON-RPC method name to call"
    )
    command_group.add_argument(
        "--params", "-p", type=str, help="JSON-RPC params as JSON string"
    )
    
    # Parse argumenten
    args = parser.parse_args()
    
    # Valideer dat we of local of remote gebruiken
    if not (args.local or args.remote):
        log("ERROR", "Specificeer verbindingsmodus: --local of --remote")
        parser.print_help()
        sys.exit(1)
    
    if args.local and args.remote:
        log("ERROR", "Kies één verbindingsmodus: --local OF --remote")
        parser.print_help()
        sys.exit(1)
        
    # Creëer client en maak verbinding
    client = MCPClient()
    
    try:
        if args.local:
            from os import getenv
            local_command = getenv("MCP_LOCAL_COMMAND")
            if not local_command:
                log("ERROR", "MCP_LOCAL_COMMAND niet ingesteld in .env bestand")
                sys.exit(1)
            success = client.connect_stdio(local_command)
        else:  # args.remote
            from os import getenv
            remote_url = getenv("MCP_SERVER_URL")
            if not remote_url:
                log("ERROR", "MCP_SERVER_URL niet ingesteld in .env bestand")
                sys.exit(1)
            success = client.connect_sse(remote_url)
        
        if not success:
            log("ERROR", "Verbinding niet gelukt")
            sys.exit(1)
            
        # Als method is opgegeven, voer deze uit
        if args.method:
            params = None
            if args.params:
                try:
                    params = json.loads(args.params)
                except json.JSONDecodeError:
                    log("ERROR", f"Ongeldige JSON in params: {args.params}")
                    sys.exit(1)
            
            response = client.send_request(args.method, params)
            print(json.dumps(response, indent=2))
            client.close()
            return
        
        # Anders start de interactieve modus
        print("MCP CLI Interactive Mode. Type 'exit' to quit.")
        while True:
            try:
                cmd = input("> ")
                if cmd.lower() in ["exit", "quit", "q"]:
                    break
                    
                # Parse command: method [params as JSON]
                parts = cmd.strip().split(" ", 1)
                method = parts[0]
                params = None
                
                if len(parts) > 1:
                    try:
                        params = json.loads(parts[1])
                    except json.JSONDecodeError:
                        log("ERROR", f"Ongeldige JSON in params: {parts[1]}")
                        continue
                
                response = client.send_request(method, params)
                print(json.dumps(response, indent=2))
            except KeyboardInterrupt:
                break
            except Exception as e:
                log("ERROR", f"Fout: {e}")
                
    finally:
        # Sluit de verbinding netjes af
        if client:
            client.close()

if __name__ == "__main__":
    main()
