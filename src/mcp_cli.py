#!/usr/bin/env python
"""
MCP CLI - Command Line Interface voor de MCP Client

Deze module biedt een command-line interface voor het verbinden met en sturen van 
verzoeken naar MCP servers, zowel lokaal (via STDIO) als remote (via SSE).
"""

import argparse
import json
import sys
import os
from pathlib import Path
from src.mcp_client import MCPClient, log, ConfigurationError, ConnectionError, CommunicationError

def print_env_help():
    """Toont hulp over het .env bestand."""
    print("\nOm de MCP CLI te configureren:")
    print("1. Kopieer .env.example naar .env in de hoofdmap van het project")
    print("2. Bewerk het .env bestand met de volgende instellingen:")
    print("   - MCP_SERVER_URL: URL voor remote verbindingen via SSE")
    print("   - MCP_LOCAL_COMMAND: Commando voor lokale verbindingen via STDIO")
    print("   - API_KEY: Optionele API-sleutel voor authenticatie")
    print("   - LOG_LEVEL: Logniveau (DEBUG, INFO, ERROR)\n")

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
    
    # Configuratieopties
    config_group = parser.add_argument_group("Configuration Options")
    config_group.add_argument(
        "--show-config", action="store_true", help="Show configuration help and exit"
    )
    
    # Parse argumenten
    args = parser.parse_args()
    
    # Toon configuratiehulp indien gevraagd
    if args.show_config:
        print_env_help()
        sys.exit(0)
    
    # Controleer of het .env bestand bestaat
    if not Path('.env').exists():
        log("ERROR", "Het .env configuratiebestand is niet gevonden.")
        print_env_help()
        sys.exit(1)
    
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
                print("Je moet een lokaal commando instellen in je .env bestand:")
                print("MCP_LOCAL_COMMAND=pad/naar/je/mcp-server")
                sys.exit(1)
            success = client.connect_stdio(local_command)
        else:  # args.remote
            from os import getenv
            remote_url = getenv("MCP_SERVER_URL")
            if not remote_url:
                log("ERROR", "MCP_SERVER_URL niet ingesteld in .env bestand")
                print("Je moet een server URL instellen in je .env bestand:")
                print("MCP_SERVER_URL=https://mijn-mcp-server.nl/events")
                sys.exit(1)
            success = client.connect_sse(remote_url)
        
        if not success:
            log("ERROR", "Verbinding niet gelukt, zie bovenstaande foutmeldingen voor meer informatie.")
            sys.exit(1)
            
        # Als method is opgegeven, voer deze uit
        if args.method:
            params = None
            if args.params:
                try:
                    params = json.loads(args.params)
                except json.JSONDecodeError as e:
                    log("ERROR", f"Ongeldige JSON in params: {args.params}")
                    print(f"Fout bij parsen van JSON: {e}")
                    print("Voorbeeld van geldige JSON: '{\"key\": \"value\"}' of '[1, 2, 3]'")
                    sys.exit(1)
            
            response = client.send_request(args.method, params)
            if "error" in response and isinstance(response["error"], str):
                log("ERROR", f"Fout bij uitvoeren {args.method}: {response['error']}")
                print(json.dumps(response, indent=2))
            else:
                print(json.dumps(response, indent=2))
            client.close()
            return
        
        # Anders start de interactieve modus
        print("MCP CLI Interactive Mode. Type 'help' voor commando's of 'exit' om af te sluiten.")
        while True:
            try:
                cmd = input("> ")
                cmd = cmd.strip()
                
                if cmd.lower() in ["exit", "quit", "q"]:
                    break
                elif cmd.lower() in ["help", "h", "?"]:
                    print("\nBeschikbare commando's:")
                    print("  exit, quit, q   - Sluit de MCP CLI af")
                    print("  help, h, ?      - Toon deze hulp")
                    print("  clear, cls      - Maak het scherm leeg")
                    print("\nJSON-RPC-verzoeken:")
                    print("  methodNaam [params als JSON]")
                    print("  Bijvoorbeeld: getVersion {}\n")
                    continue
                elif cmd.lower() in ["clear", "cls"]:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue
                elif not cmd:
                    continue
                    
                # Parse command: method [params as JSON]
                parts = cmd.strip().split(" ", 1)
                method = parts[0]
                params = None
                
                if len(parts) > 1:
                    try:
                        params = json.loads(parts[1])
                    except json.JSONDecodeError as e:
                        log("ERROR", f"Ongeldige JSON in params: {parts[1]}")
                        print(f"Fout bij parsen van JSON: {e}")
                        print("Voorbeeld van geldige JSON: '{\"key\": \"value\"}' of '[1, 2, 3]'")
                        continue
                
                response = client.send_request(method, params)
                if "error" in response and isinstance(response["error"], str):
                    log("ERROR", f"Fout bij uitvoeren {method}: {response['error']}")
                    print(json.dumps(response, indent=2))
                else:
                    print(json.dumps(response, indent=2))
            except KeyboardInterrupt:
                print("\nProgramma onderbroken met Ctrl+C")
                break
            except EOFError:
                print("\nEinde van input (EOF)")
                break
            except Exception as e:
                log("ERROR", f"Onverwachte fout: {e}")
                
    except ConfigurationError as e:
        log("ERROR", f"Configuratiefout: {e}")
        print_env_help()
        sys.exit(1)
    except ConnectionError as e:
        log("ERROR", f"Verbindingsfout: {e}")
        sys.exit(1)
    except Exception as e:
        log("ERROR", f"Onverwachte fout: {e}")
        sys.exit(1)
    finally:
        # Sluit de verbinding netjes af
        if 'client' in locals() and client:
            try:
                client.close()
            except Exception as e:
                log("ERROR", f"Fout bij afsluiten client: {e}")

if __name__ == "__main__":
    main()
