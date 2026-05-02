import argparse
import json
import socket
import threading
import time


class TrafficServer:
    """Central hub that shares state between multiple junction simulations."""

    def __init__(self, host="127.0.0.1", port=8765):
        self.host = host
        self.port = port
        self._junctions = {}
        self._clients = {}
        self._lock = threading.Lock()
        self._send_lock = threading.Lock()

    def serve_forever(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((self.host, self.port))
            server_sock.listen()
            print(f"Traffic server listening on {self.host}:{self.port}")

            while True:
                client_sock, address = server_sock.accept()
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, address),
                    daemon=True,
                )
                thread.start()

    def _handle_client(self, client_sock, address):
        junction_id = None
        with client_sock:
            try:
                reader = client_sock.makefile("r", encoding="utf-8")
                for line in reader:
                    message = json.loads(line)
                    message_type = message.get("type")

                    if message_type == "register":
                        junction_id = self._register_client(client_sock, message, address)
                        print(f"Registered junction {junction_id} from {address[0]}:{address[1]}")
                        self._broadcast_grid_state()
                    elif message_type == "junction_update":
                        junction_id = self._update_junction(client_sock, message, address, junction_id)
                        self._broadcast_grid_state()
            except (OSError, json.JSONDecodeError) as exc:
                print(f"Client {address[0]}:{address[1]} disconnected: {exc}")
            finally:
                if junction_id is not None:
                    with self._lock:
                        self._clients.pop(junction_id, None)
                        if junction_id in self._junctions:
                            self._junctions[junction_id]["connected"] = False
                            self._junctions[junction_id]["last_seen"] = time.time()
                    self._broadcast_grid_state()
                    print(f"Junction {junction_id} disconnected")

    def _register_client(self, client_sock, message, address):
        junction_id = str(message.get("junction_id") or f"{address[0]}:{address[1]}")
        grid_position = message.get("grid_position", [0, 0])
        with self._lock:
            self._clients[junction_id] = client_sock
            existing_payload = self._junctions.get(junction_id, {}).get("payload", {})
            self._junctions[junction_id] = {
                "junction_id": junction_id,
                "grid_position": grid_position,
                "payload": existing_payload,
                "connected": True,
                "last_seen": time.time(),
            }
        return junction_id

    def _update_junction(self, client_sock, message, address, current_junction_id):
        junction_id = str(message.get("junction_id") or current_junction_id or f"{address[0]}:{address[1]}")
        grid_position = message.get("grid_position", [0, 0])
        payload = message.get("payload", {})
        with self._lock:
            self._clients[junction_id] = client_sock
            self._junctions[junction_id] = {
                "junction_id": junction_id,
                "grid_position": grid_position,
                "payload": payload,
                "connected": True,
                "last_seen": time.time(),
            }
        return junction_id

    def _broadcast_grid_state(self):
        with self._lock:
            message = {
                "type": "grid_state",
                "server_time": time.time(),
                "junctions": dict(self._junctions),
            }
            clients = list(self._clients.items())

        data = (json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8")
        disconnected = []
        with self._send_lock:
            for junction_id, client_sock in clients:
                try:
                    client_sock.sendall(data)
                except OSError:
                    disconnected.append(junction_id)

        if disconnected:
            with self._lock:
                for junction_id in disconnected:
                    self._clients.pop(junction_id, None)
                    if junction_id in self._junctions:
                        self._junctions[junction_id]["connected"] = False
                        self._junctions[junction_id]["last_seen"] = time.time()


def parse_args():
    parser = argparse.ArgumentParser(description="Central traffic server for the SDL3 traffic simulation.")
    parser.add_argument("--host", default="127.0.0.1", help="Interface to bind the server to.")
    parser.add_argument("--port", type=int, default=8765, help="TCP port to listen on.")
    return parser.parse_args()


def main():
    args = parse_args()
    TrafficServer(args.host, args.port).serve_forever()


if __name__ == "__main__":
    main()
