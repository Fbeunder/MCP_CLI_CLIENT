# MCP CLI Client

Een Command Line Interface voor het werken met MCP (Machine Communication Protocol) servers via zowel lokale verbindingen (STDIO) als remote verbindingen (SSE).

## Overzicht

De MCP CLI Client stelt gebruikers in staat om:
- Te verbinden met lokale MCP-servers via STDIO
- Te verbinden met remote MCP-servers via SSE (Server-Sent Events)
- JSON-RPC verzoeken te sturen naar verbonden servers
- Te werken in zowel command-line modus als interactieve modus
- Als een Python module te integreren in andere projecten

## Installatie

1. Clone de repository:
   ```bash
   git clone https://github.com/Fbeunder/MCP_CLI_CLIENT.git
   cd MCP_CLI_CLIENT
   ```

2. Maak een virtuele omgeving aan (optioneel maar aanbevolen):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Op Windows: venv\Scripts\activate
   ```

3. Installeer de benodigde packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Configureer de applicatie:
   ```bash
   cp .env.example .env
   # Bewerk .env met je eigen configuratie
   ```

5. Om als Python pakket te installeren:
   ```bash
   pip install -e .
   ```

## Gebruik als Command Line Tool

### Basis commando's

```bash
# Verbinden met een lokale MCP-server en een verzoek uitvoeren
python main.py --local --method methodName --params '{"param1": "value1"}'

# Verbinden met een remote MCP-server en een verzoek uitvoeren
python main.py --remote --method methodName --params '{"param1": "value1"}'

# Starten in interactieve modus met een lokale server
python main.py --local
```

### Interactieve modus

In de interactieve modus kun je commando's invoeren in het formaat:
```
methodName {"param1": "value1", "param2": "value2"}
```

Typ `exit`, `quit` of `q` om de interactieve modus te verlaten.

## Gebruik als Python Module

De MCP CLI Client kan ook worden gebruikt als een Python module in je eigen projecten:

```python
from mcp_cli_client import MCPClient

# Maak een nieuwe client instantie
client = MCPClient()

# Verbind met een lokale MCP server
client.connect_stdio("path/to/local/mcp/server")
# OF verbind met een remote server
# client.connect_sse("https://mcp-server.example.com/events")

# Stuur verzoeken
response = client.send_request("getVersion")
print(response)

# Stuur verzoeken met parameters
response = client.send_request("echo", {"message": "Hello, MCP!"})
print(response)

# Sluit de verbinding
client.close()
```

### Installatie als module

Om de MCP CLI Client als module te installeren in andere projecten:

```bash
# Vanuit de repo directory
pip install -e .

# OF direct vanaf GitHub
pip install git+https://github.com/Fbeunder/MCP_CLI_CLIENT.git
```

### Uitgebreid voorbeeld

Bekijk `examples/module_example.py` voor een uitgebreid voorbeeld van het gebruik als module.

## Configuratie

Configuratie wordt geladen uit het `.env` bestand, met de volgende opties:

- `MCP_SERVER_URL`: URL voor de remote SSE server
- `MCP_LOCAL_COMMAND`: Opdracht om een lokale server te starten via STDIO
- `API_KEY`: Optionele API-sleutel voor authenticatie
- `LOG_LEVEL`: Logniveau (DEBUG, INFO, ERROR)

## Testen

Het project bevat een uitgebreide testsuite met unit tests en integratietests.

### Tests uitvoeren

1. Installeer de test dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Voer alle tests uit:
   ```bash
   pytest
   ```

3. Voer tests uit met coverage rapportage:
   ```bash
   pytest --cov=src
   ```

### Teststructuur

- `tests/test_mcp_client.py`: Unit tests voor de MCPClient class
- `tests/test_mcp_cli.py`: Unit tests voor de command-line interface
- `tests/test_integration.py`: Integratietests die de verschillende componenten samen testen

## API Documentatie

### MCPClient

De `MCPClient` klasse biedt de volgende methoden:

- `connect_stdio(command=None)`: Verbind met een lokale MCP server via STDIO
- `connect_sse(url=None)`: Verbind met een remote MCP server via SSE
- `send_request(method, params=None)`: Stuur een JSON-RPC verzoek
- `close()`: Sluit de verbinding

### Exceptions

- `ConfigurationError`: Fout bij laden of verwerken van configuratie
- `ConnectionError`: Fout bij het maken van een verbinding
- `CommunicationError`: Fout bij communicatie met de MCP server

## Licentie

[MIT](LICENSE)
