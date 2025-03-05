# MCP CLI Client

Een Command Line Interface voor het werken met MCP (Machine Communication Protocol) servers via zowel lokale verbindingen (STDIO) als remote verbindingen (SSE).

## Overzicht

De MCP CLI Client stelt gebruikers in staat om:
- Te verbinden met lokale MCP-servers via STDIO
- Te verbinden met remote MCP-servers via SSE (Server-Sent Events)
- JSON-RPC verzoeken te sturen naar verbonden servers
- Te werken in zowel command-line modus als interactieve modus

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

## Gebruik

### Basis commando's

```bash
# Verbinden met een lokale MCP-server en een verzoek uitvoeren
python -m src.mcp_cli --local --method methodName --params '{"param1": "value1"}'

# Verbinden met een remote MCP-server en een verzoek uitvoeren
python -m src.mcp_cli --remote --method methodName --params '{"param1": "value1"}'

# Starten in interactieve modus met een lokale server
python -m src.mcp_cli --local
```

### Interactieve modus

In de interactieve modus kun je commando's invoeren in het formaat:
```
methodName {"param1": "value1", "param2": "value2"}
```

Typ `exit`, `quit` of `q` om de interactieve modus te verlaten.

## Configuratie

Configuratie wordt geladen uit het `.env` bestand, met de volgende opties:

- `MCP_SERVER_URL`: URL voor de remote SSE server
- `MCP_LOCAL_COMMAND`: Opdracht om een lokale server te starten via STDIO
- `API_KEY`: Optionele API-sleutel voor authenticatie
- `LOG_LEVEL`: Logniveau (DEBUG, INFO, ERROR)

## Licentie

[MIT](LICENSE)
