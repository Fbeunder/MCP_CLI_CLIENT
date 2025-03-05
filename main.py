#!/usr/bin/env python
"""
MCP CLI Client - Entrypoint Script

Dit is het hoofdentrypoint voor de MCP CLI Client applicatie. 
Door dit script uit te voeren vanaf de projectroot, kunnen gebruikers eenvoudig
toegang krijgen tot alle functionaliteit zonder zich zorgen te maken over Python
module-importpaden.
"""

import sys
import os
from pathlib import Path
from src.mcp_cli import main as cli_main

def check_environment():
    """
    Controleert of de omgeving correct is ingesteld.
    
    Returns:
        bool: True als de omgeving klaar is voor gebruik, anders False
    """
    # Controleer of we in de juiste map zijn (waar dit script zich bevindt)
    if not Path('src').is_dir() or not Path('src/mcp_cli.py').is_file():
        print("Fout: De applicatie moet worden uitgevoerd vanuit de hoofdmap van het project.")
        print(f"Huidige map: {os.getcwd()}")
        return False
    
    # Controleer of het .env bestand of .env.example bestaat
    if not Path('.env').is_file():
        if Path('.env.example').is_file():
            print("Waarschuwing: Geen .env bestand gevonden, maar .env.example is aanwezig.")
            print("Tip: Kopieer .env.example naar .env en pas deze aan voor jouw configuratie.")
        else:
            print("Fout: Geen .env of .env.example bestand gevonden.")
            print("Controleer of je in de juiste map bent en of de bestanden aanwezig zijn.")
            return False
    
    return True

if __name__ == "__main__":
    """
    Start de MCP CLI applicatie.
    Alle command-line argumenten worden doorgegeven aan de mcp_cli module.
    """
    try:
        # Controleer de omgeving voordat we beginnen
        if not check_environment():
            sys.exit(1)
            
        # Start de CLI applicatie
        cli_main()
    except KeyboardInterrupt:
        print("\nProgramma onderbroken door gebruiker")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        print("\nEr is een onverwachte fout opgetreden.")
        print("Als dit probleem aanhoudt, controleer dan het volgende:")
        print("- Je hebt de laatste versie van de applicatie")
        print("- Je .env bestand is correct ingesteld")
        print("- De MCP server waarmee je verbindt is actief")
        sys.exit(1)
