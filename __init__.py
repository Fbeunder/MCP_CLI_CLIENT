"""
MCP CLI Client Root Package

Dit package maakt het mogelijk om de MCP CLI client te gebruiken als een Python module.
"""

from src.mcp_client import MCPClient, log, ConfigurationError, ConnectionError, CommunicationError

# Versie informatie
__version__ = "0.1.0"
