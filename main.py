#!/usr/bin/env python
"""
MCP CLI Client - Entrypoint Script

Dit is het hoofdentrypoint voor de MCP CLI Client applicatie. 
Door dit script uit te voeren vanaf de projectroot, kunnen gebruikers eenvoudig
toegang krijgen tot alle functionaliteit zonder zich zorgen te maken over Python
module-importpaden.
"""

import sys
from src.mcp_cli import main as cli_main


if __name__ == "__main__":
    """
    Start de MCP CLI applicatie.
    Alle command-line argumenten worden doorgegeven aan de mcp_cli module.
    """
    try:
        cli_main()
    except KeyboardInterrupt:
        print("\nProgramma onderbroken door gebruiker")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
