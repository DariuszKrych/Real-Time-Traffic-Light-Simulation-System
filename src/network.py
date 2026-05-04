import json
import socket
import threading
import time


class TrafficNetworkClient:
    """Background client for the optional multi-junction traffic server."""

    def __init__(self, junction_id, host="127.0.0.1", port=8765, grid_x=0, grid_y=0):
        self.junction_id = junction_id
        self.host = host
        self.port = port
        self.grid_x = grid_x
        self.grid_y = grid_y

        self._sock = None
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._latest_grid = {}
        self._status = "disconnected"
        self._last_error = ""
        self._outbox = None
        self._receive_buffer = ""

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self._close_socket()
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def update_junction_state(self, payload):
        message = {
            "type": "junction_update",
            "junction_id": self.junction_id,
            "grid_position": [self.grid_x, self.grid_y],
            "timestamp": time.time(),
            "payload": payload,
        }
        with self._lock:
            self._outbox = message

    def get_snapshot(self):
        with self._lock:
            peer_count = max(0, len(self._latest_grid) - (1 if self.junction_id in self._latest_grid else 0))
            return {
                "status": self._status,
                "last_error": self._last_error,
                "peer_count": peer_count,
                "grid": dict(self._latest_grid),
            }

    def _run(self):
        while self._running:
            try:
                self._set_status("connecting")
                self._connect()
                self._send({
                    "type": "register",
                    "junction_id": self.junction_id,
                    "grid_position": [self.grid_x, self.grid_y],
                })
                self._set_status("connected", "")

                while self._running:
                    self._flush_latest_update()
                    self._read_available_messages()
                    time.sleep(0.1)
            except OSError as exc:
                self._set_status("disconnected", str(exc))
                self._close_socket()
                time.sleep(1.0)

    def _connect(self):
        self._sock = socket.create_connection((self.host, self.port), timeout=3.0)
        self._sock.settimeout(0.1)
        self._receive_buffer = ""

    def _flush_latest_update(self):
        with self._lock:
            message = self._outbox
            self._outbox = None
        if message is not None:
            self._send(message)

    def _read_available_messages(self):
        if self._sock is None:
            return
        while self._running:
            try:
                chunk = self._sock.recv(4096)
            except socket.timeout:
                return
            if not chunk:
                raise OSError("server closed the connection")
            self._receive_buffer += chunk.decode("utf-8")
            while "\n" in self._receive_buffer:
                line, self._receive_buffer = self._receive_buffer.split("\n", 1)
                if not line.strip():
                    continue
                message = json.loads(line)
                if message.get("type") == "grid_state":
                    with self._lock:
                        self._latest_grid = message.get("junctions", {})

    def _send(self, message):
        if self._sock is None:
            return
        data = json.dumps(message, separators=(",", ":")) + "\n"
        self._sock.sendall(data.encode("utf-8"))

    def _set_status(self, status, error=None):
        with self._lock:
            self._status = status
            if error is not None:
                self._last_error = error

    def _close_socket(self):
        sock = self._sock
        self._sock = None
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
