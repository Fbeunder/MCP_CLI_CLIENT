import os
import sys
import json
import threading
import subprocess
import requests
import time
import queue
from pathlib import Path
from dotenv import load_dotenv

# Custom exception classes
class MCPClientError(Exception):
    """Basisklasse voor alle MCP Client-gerelateerde fouten."""
    pass

class ConfigurationError(MCPClientError):
    """Fout bij laden of verwerken van configuratie."""
    pass

class ConnectionError(MCPClientError):
    """Fout bij het maken van een verbinding."""
    pass

class CommunicationError(MCPClientError):
    """Fout bij communicatie met de MCP server."""
    pass

# Laad configuratie uit .env bestand
env_loaded = False
dotenv_path = Path('.env')
if dotenv_path.exists():
    load_dotenv()
    env_loaded = True

# Haal configuratiewaarden op met fallbacks
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "")
MCP_LOCAL_COMMAND = os.getenv("MCP_LOCAL_COMMAND", "")
API_KEY = os.getenv("API_KEY", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Logging configuratie
LOG_LEVELS = {"DEBUG": 10, "INFO": 20, "ERROR": 40}
current_log_level = LOG_LEVELS.get(LOG_LEVEL, 20)

def log(level, message):
    """Logt een bericht als het niveau hoog genoeg is."""
    if LOG_LEVELS.get(level, 0) >= current_log_level:
        print(f"[{level}] {message}")

def check_config():
    """Controleert of de nodige configuratie aanwezig is en geeft bruikbare feedback.
    
    Returns:
        bool: True als het .env bestand is geladen, anders False
    """
    messages = []
    
    if not env_loaded:
        messages.append(
            "Het .env bestand kon niet worden gevonden. "
            "Kopieer .env.example naar .env en pas deze aan."
        )
    
    if not messages:
        return True
    
    log("ERROR", "\n".join(messages))
    return False

# MCPClient class definitie
class MCPClient:
    def __init__(self):
        self.connection = None  # Kan een proces (STDIO) of SSE session zijn
        self.transport = None  # "stdio" of "sse"
        self._id_counter = 1   # Unieke ID teller voor JSON-RPC requests
        self._response_queue = queue.Queue()
        self._stop_event = threading.Event()
        
        # Configuratiecontrole bij initialisatie
        if not check_config():
            log("INFO", "De client is geïnitialiseerd met ontbrekende configuratie.")

    def connect_stdio(self, command=None):
        """Start een lokaal MCP-serverproces en verbind via STDIO.
        
        Args:
            command (str, optional): Het commando om het MCP-serverproces te starten.
                                    Als niet opgegeven, wordt MCP_LOCAL_COMMAND uit .env gebruikt.
        
        Returns:
            bool: True als de verbinding succesvol is, anders False
            
        Raises:
            ConfigurationError: Als geen geldig commando is opgegeven of gevonden
            ConnectionError: Als het proces niet kon worden gestart
        """
        try:
            # Gebruik opgegeven commando of uit configuratie
            local_command = command or MCP_LOCAL_COMMAND
            
            if not local_command:
                raise ConfigurationError(
                    "MCP_LOCAL_COMMAND niet ingesteld in .env bestand of als parameter.\n"
                    "Stel deze in met het pad naar het lokale MCP-serverproces."
                )
            
            # Start het externe proces (MCP server) via subprocess
            log("INFO", f"Start lokaal MCP proces: {local_command}")
            # `bufsize=1` en `universal_newlines=True` voor real-time line-buffering
            process = subprocess.Popen(
                local_command.split(), 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                bufsize=1
            )
            
            # Controleer of het proces correct is gestart
            if process.poll() is not None:
                stderr_output = process.stderr.read()
                raise ConnectionError(
                    f"Kon het lokale proces niet starten of het proces is meteen gestopt.\n"
                    f"Foutuitvoer: {stderr_output}"
                )
                
            self.connection = process
            self.transport = "stdio"
            
            # Start een achtergrondthread om STDOUT te lezen
            threading.Thread(target=self._stdio_listener, args=(process,), daemon=True).start()
            return True
        except ConfigurationError as e:
            log("ERROR", f"Configuratiefout: {e}")
            return False
        except ConnectionError as e:
            log("ERROR", f"Verbindingsfout: {e}")
            return False
        except Exception as e:
            log("ERROR", f"Onverwachte fout bij starten lokaal proces: {e}")
            return False

    def _stdio_listener(self, process):
        """Leest continu uit het STDOUT van een lokaal MCP-proces.
        
        Args:
            process: Het subprocess object van het lokale MCP-serverproces
        """
        for line in process.stdout:
            if not line:
                continue
            line = line.strip()
            if line == "":
                continue
            try:
                # Verwerk alleen geldige JSON-lijnen
                data = json.loads(line)
            except json.JSONDecodeError:
                log("DEBUG", f"Genegeerd (geen JSON): {line}")
                continue
            # Plaats ontvangen bericht in de wachtrij
            self._response_queue.put(data)
            log("DEBUG", f"STDIO ontvangen: {data}")
            if self._stop_event.is_set():
                break

        # Controleer of het proces onverwacht is gestopt
        if not self._stop_event.is_set() and process.poll() is not None:
            stderr_output = process.stderr.read() if process.stderr else "Geen foutuitvoer beschikbaar."
            error_msg = f"Lokaal proces is onverwacht gestopt. Foutuitvoer: {stderr_output}"
            log("ERROR", error_msg)
            self._response_queue.put({"error": error_msg})

    def connect_sse(self, url=None):
        """Verbind met een remote MCP server via SSE (Server-Sent Events).
        
        Args:
            url (str, optional): De URL van de MCP-server. Als niet opgegeven, wordt 
                                MCP_SERVER_URL uit .env gebruikt.
        
        Returns:
            bool: True als de verbinding succesvol is, anders False
            
        Raises:
            ConfigurationError: Als geen geldige URL is opgegeven of gevonden
            ConnectionError: Als er geen verbinding kon worden gemaakt met de server
        """
        try:
            # Gebruik opgegeven URL of uit configuratie
            server_url = url or MCP_SERVER_URL
            
            if not server_url:
                raise ConfigurationError(
                    "MCP_SERVER_URL niet ingesteld in .env bestand of als parameter.\n"
                    "Stel deze in met de URL van de remote MCP server."
                )
            
            # Valideer URL format
            if not server_url.startswith(('http://', 'https://')):
                raise ConfigurationError(
                    f"Ongeldige server URL: {server_url}.\n"
                    f"URL moet beginnen met http:// of https://."
                )
            
            # Start SSE-stream in aparte thread
            headers = {}
            if API_KEY:
                headers["Authorization"] = f"Bearer {API_KEY}"
            log("INFO", f"Verbind met remote MCP server via SSE: {server_url}")
            
            # Controleer verbinding voordat we de thread starten
            try:
                response = requests.get(server_url, headers=headers, stream=True, timeout=5)
                response.raise_for_status()  # Raise exception voor HTTP-fouten
            except requests.exceptions.RequestException as e:
                raise ConnectionError(
                    f"Kan geen verbinding maken met de MCP server: {str(e)}.\n"
                    f"Controleer of de server actief is en bereikbaar op {server_url}."
                )
            
            threading.Thread(target=self._sse_listener, args=(server_url, headers), daemon=True).start()
            self.transport = "sse"
            return True
        except ConfigurationError as e:
            log("ERROR", f"Configuratiefout: {e}")
            return False
        except ConnectionError as e:
            log("ERROR", f"Verbindingsfout: {e}")
            return False
        except Exception as e:
            log("ERROR", f"Onverwachte fout bij verbinden via SSE: {e}")
            return False

    def _sse_listener(self, url, headers):
        """Leest continu van de SSE endpoint.
        
        Args:
            url (str): De URL van de MCP-server
            headers (dict): De HTTP-headers voor de request
        """
        retry_delay = 1  # initiële retry delay in seconden
        max_retry_delay = 30  # maximale retry delay
        
        while not self._stop_event.is_set():
            try:
                # Stream via requests (EventSource)
                with requests.get(url, headers=headers, stream=True, timeout=30) as response:
                    # Reset retry delay bij succesvolle verbinding
                    retry_delay = 1
                    
                    # Controleer HTTP status code
                    if response.status_code != 200:
                        error_msg = f"Server antwoordde met status code {response.status_code}: {response.reason}"
                        log("ERROR", error_msg)
                        self._response_queue.put({"error": error_msg})
                        break
                    
                    for line in response.iter_lines():
                        if self._stop_event.is_set():
                            break
                        if not line:
                            continue  # hartslag of lege lijn
                        decoded = line.decode('utf-8')
                        # SSE-gegevens beginnen vaak met 'data: '
                        if decoded.startswith("data:"):
                            json_str = decoded[len("data:"):].strip()
                            if json_str:
                                try:
                                    data = json.loads(json_str)
                                except json.JSONDecodeError:
                                    log("DEBUG", f"Genegeerd (geen JSON): {decoded}")
                                    continue
                                # Zet ontvangen bericht in wachtrij
                                self._response_queue.put(data)
                                log("DEBUG", f"SSE ontvangen: {data}")
            except requests.exceptions.Timeout:
                if not self._stop_event.is_set():
                    log("ERROR", f"Timeout bij SSE verbinding. Probeer opnieuw over {retry_delay} seconden.")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_retry_delay)  # exponential backoff
            except requests.exceptions.ConnectionError:
                if not self._stop_event.is_set():
                    log("ERROR", f"Verbinding verbroken. Probeer opnieuw over {retry_delay} seconden.")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_retry_delay)  # exponential backoff
            except Exception as e:
                log("ERROR", f"SSE luisterfout: {e}")
                self._response_queue.put({"error": str(e)})
                break

    def send_request(self, method, params=None):
        """Stuur een JSON-RPC verzoek naar de MCP-server.
        
        Args:
            method (str): De JSON-RPC methode om aan te roepen
            params (dict/list, optional): De parameters voor de JSON-RPC methode
            
        Returns:
            dict: De JSON-RPC response, of een dict met een error-sleutel bij fouten
            
        Raises:
            CommunicationError: Als er een fout optreedt bij het versturen van het verzoek
        """
        if self.transport is None:
            error_msg = "Geen verbinding. Gebruik eerst 'connect_stdio' of 'connect_sse'."
            log("ERROR", error_msg)
            return {"error": error_msg}
            
        # Stel JSON-RPC bericht samen
        request_id = self._id_counter
        self._id_counter += 1
        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method
        }
        if params is not None:
            message["params"] = params

        try:
            if self.transport == "stdio":
                # Stuur bericht naar STDIN van het subprocess
                if not self.connection or self.connection.poll() is not None:
                    raise CommunicationError("De verbinding met het lokale proces is verbroken.")
                    
                self.connection.stdin.write(json.dumps(message) + "\n")
                self.connection.stdin.flush()
                log("INFO", f">>> Verzoek verzonden (STDIO): {message}")
            elif self.transport == "sse":
                # Verstuur HTTP POST voor SSE
                post_url = MCP_SERVER_URL  # gebruik basis URL voor POST
                if not post_url:
                    raise ConfigurationError("MCP_SERVER_URL is niet ingesteld.")
                    
                headers = {"Content-Type": "application/json"}
                if API_KEY:
                    headers["Authorization"] = f"Bearer {API_KEY}"
                log("INFO", f">>> Verzoek verzonden (HTTP POST): {message}")
                
                try:
                    response = requests.post(post_url, headers=headers, json=message, timeout=10)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    raise CommunicationError(f"Fout bij HTTP-verzoek: {str(e)}")
                    
            # Wacht op antwoord in de wachtrij (met timeout voor veiligheid)
            try:
                response = self._response_queue.get(timeout=10)
                return response
            except queue.Empty:
                error_msg = "Time-out bij wachten op antwoord."
                log("ERROR", error_msg)
                return {"error": error_msg}
        except ConfigurationError as e:
            log("ERROR", f"Configuratiefout: {e}")
            return {"error": str(e)}
        except CommunicationError as e:
            log("ERROR", f"Communicatiefout: {e}")
            return {"error": str(e)}
        except Exception as e:
            log("ERROR", f"Onverwachte fout bij versturen verzoek: {e}")
            return {"error": str(e)}

    def close(self):
        """Sluit de verbinding af (beëindig proces of streaming)."""
        self._stop_event.set()
        if self.transport == "stdio":
            try:
                # Beëindig lokaal proces netjes
                if self.connection:
                    self.connection.terminate()
                    try:
                        self.connection.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        log("ERROR", "Proces reageert niet, forceer afsluiten.")
                        self.connection.kill()
                    log("INFO", "Lokaal proces gestopt.")
            except Exception as e:
                log("ERROR", f"Fout bij stoppen lokaal proces: {e}")
        elif self.transport == "sse":
            # Voor SSE volstaat het stoppen van de luisterthread via _stop_event
            log("INFO", "Remote SSE-verbinding gesloten.")
        self.transport = None
        self.connection = None
        # Leeg eventueel de response queue
        with self._response_queue.mutex:
            self._response_queue.queue.clear()
