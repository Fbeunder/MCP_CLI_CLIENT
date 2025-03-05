import os
import sys
import json
import threading
import subprocess
import requests
import time
import queue
from dotenv import load_dotenv

# Laad configuratie uit .env bestand
load_dotenv()
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
MCP_LOCAL_COMMAND = os.getenv("MCP_LOCAL_COMMAND")
API_KEY = os.getenv("API_KEY", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Logging configuratie
LOG_LEVELS = {"DEBUG": 10, "INFO": 20, "ERROR": 40}
current_log_level = LOG_LEVELS.get(LOG_LEVEL, 20)

def log(level, message):
    """Logt een bericht als het niveau hoog genoeg is."""
    if LOG_LEVELS.get(level, 0) >= current_log_level:
        print(f"[{level}] {message}")

# MCPClient class definitie
class MCPClient:
    def __init__(self):
        self.connection = None  # Kan een proces (STDIO) of SSE session zijn
        self.transport = None  # "stdio" of "sse"
        self._id_counter = 1   # Unieke ID teller voor JSON-RPC requests
        self._response_queue = queue.Queue()
        self._stop_event = threading.Event()

    def connect_stdio(self, command):
        """Start een lokaal MCP-serverproces en verbind via STDIO."""
        try:
            # Start het externe proces (MCP server) via subprocess
            log("INFO", f"Start lokaal MCP proces: {command}")
            # `bufsize=1` en `universal_newlines=True` voor real-time line-buffering
            process = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            self.connection = process
            self.transport = "stdio"
            
            # Start een achtergrondthread om STDOUT te lezen
            threading.Thread(target=self._stdio_listener, args=(process,), daemon=True).start()
            return True
        except Exception as e:
            log("ERROR", f"Fout bij starten lokaal proces: {e}")
            return False

    def _stdio_listener(self, process):
        """Leest continu uit het STDOUT van een lokaal MCP-proces."""
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

    def connect_sse(self, url):
        """Verbind met een remote MCP server via SSE (Server-Sent Events)."""
        try:
            # Start SSE-stream in aparte thread
            headers = {}
            if API_KEY:
                headers["Authorization"] = f"Bearer {API_KEY}"
            log("INFO", f"Verbind met remote MCP server via SSE: {url}")
            threading.Thread(target=self._sse_listener, args=(url, headers), daemon=True).start()
            self.transport = "sse"
            return True
        except Exception as e:
            log("ERROR", f"Fout bij verbinden via SSE: {e}")
            return False

    def _sse_listener(self, url, headers):
        """Leest continu van de SSE endpoint."""
        try:
            # Stream via requests (EventSource)
            with requests.get(url, headers=headers, stream=True) as response:
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
        except Exception as e:
            log("ERROR", f"SSE luisterfout: {e}")
            self._response_queue.put({"error": str(e)})

    def send_request(self, method, params=None):
        """Stuur een JSON-RPC verzoek naar de MCP-server."""
        if self.transport is None:
            log("ERROR", "Geen verbinding. Gebruik eerst 'connect'.")
            return None
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
                self.connection.stdin.write(json.dumps(message) + "\n")
                self.connection.stdin.flush()
                log("INFO", f">>> Verzoek verzonden (STDIO): {message}")
            elif self.transport == "sse":
                # Verstuur HTTP POST voor SSE
                post_url = MCP_SERVER_URL  # gebruik basis URL voor POST
                headers = {"Content-Type": "application/json"}
                if API_KEY:
                    headers["Authorization"] = f"Bearer {API_KEY}"
                log("INFO", f">>> Verzoek verzonden (HTTP POST): {message}")
                requests.post(post_url, headers=headers, json=message)
            # Wacht op antwoord in de wachtrij (met timeout voor veiligheid)
            try:
                response = self._response_queue.get(timeout=10)
                return response
            except queue.Empty:
                log("ERROR", "Time-out bij wachten op antwoord.")
                return {"error": "No response (timeout)"}
        except Exception as e:
            log("ERROR", f"Fout bij versturen verzoek: {e}")
            return {"error": str(e)}

    def close(self):
        """Sluit de verbinding af (beëindig proces of streaming)."""
        self._stop_event.set()
        if self.transport == "stdio":
            try:
                # Beëindig lokaal proces netjes
                self.connection.terminate()
                self.connection.wait(timeout=5)
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