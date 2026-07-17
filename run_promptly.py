"""Start Promptly locally and open it in the user's default browser."""

from __future__ import annotations

import os
import secrets
import socket
import threading
import time
import webbrowser

from app import app
from werkzeug.serving import make_server


HOST = "127.0.0.1"
DEFAULT_PORT = 5000
PORT_ATTEMPTS = 20
CLIENT_CLOSE_GRACE_SECONDS = 3.0
CLIENT_HEARTBEAT_TIMEOUT_SECONDS = 90.0
CLIENT_CHECK_INTERVAL_SECONDS = 0.5


class BrowserSessionMonitor:
    """Stop Promptly after its final browser tab has gone away."""

    def __init__(
        self,
        shutdown_callback,
        *,
        close_grace_seconds: float = CLIENT_CLOSE_GRACE_SECONDS,
        heartbeat_timeout_seconds: float = CLIENT_HEARTBEAT_TIMEOUT_SECONDS,
        check_interval_seconds: float = CLIENT_CHECK_INTERVAL_SECONDS,
    ) -> None:
        self.shutdown_callback = shutdown_callback
        self.close_grace_seconds = close_grace_seconds
        self.heartbeat_timeout_seconds = heartbeat_timeout_seconds
        self.check_interval_seconds = check_interval_seconds
        self._clients: dict[str, float] = {}
        self._event_sequences: dict[str, int] = {}
        self._saw_client = False
        self._empty_since: float | None = None
        self._shutdown_requested = False
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def notify(
        self,
        event: str,
        client_id: str,
        sequence: int,
        *,
        now: float | None = None,
    ) -> None:
        """Record an ordered heartbeat or close event from one browser tab."""
        timestamp = time.monotonic() if now is None else now
        with self._lock:
            previous_sequence = self._event_sequences.get(client_id, -1)
            if sequence <= previous_sequence:
                return
            self._event_sequences[client_id] = sequence
            self._saw_client = True
            if event == "heartbeat":
                self._clients[client_id] = timestamp
                self._empty_since = None
            elif event == "close":
                self._clients.pop(client_id, None)
                if not self._clients:
                    self._empty_since = timestamp

    def check(self, *, now: float | None = None) -> bool:
        """Evaluate client state once and request shutdown when appropriate."""
        timestamp = time.monotonic() if now is None else now
        should_shutdown = False
        with self._lock:
            expired = [
                client_id
                for client_id, last_seen in self._clients.items()
                if timestamp - last_seen >= self.heartbeat_timeout_seconds
            ]
            for client_id in expired:
                self._clients.pop(client_id, None)

            if self._clients:
                self._empty_since = None
            elif self._saw_client:
                if self._empty_since is None:
                    self._empty_since = timestamp
                if (
                    not self._shutdown_requested
                    and timestamp - self._empty_since >= self.close_grace_seconds
                ):
                    self._shutdown_requested = True
                    should_shutdown = True

        if should_shutdown:
            self.shutdown_callback()
        return should_shutdown

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._watch,
            name="promptly-browser-monitor",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=2)

    def _watch(self) -> None:
        while not self._stop_event.wait(self.check_interval_seconds):
            if self.check():
                return


def requested_port() -> int:
    """Return a valid preferred port from the environment, or the default."""
    try:
        port = int(os.getenv("PROMPTLY_PORT", str(DEFAULT_PORT)))
    except ValueError:
        return DEFAULT_PORT
    return port if 1 <= port <= 65_535 else DEFAULT_PORT


def find_available_port(preferred_port: int, attempts: int = PORT_ATTEMPTS) -> int:
    """Find an available localhost port, starting with the preferred port."""
    for port in range(preferred_port, min(preferred_port + attempts, 65_536)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
            try:
                candidate.bind((HOST, port))
            except OSError:
                continue
            return port
    raise RuntimeError(
        f"Promptly could not find an available port between {preferred_port} "
        f"and {min(preferred_port + attempts - 1, 65_535)}."
    )


def main() -> None:
    port = find_available_port(requested_port())
    url = f"http://{HOST}:{port}/"
    print(f"Promptly is starting at {url}")
    print("Close all Promptly browser tabs to stop the local service automatically.")

    server = make_server(HOST, port, app, threaded=True)
    lifecycle_token = secrets.token_urlsafe(24)
    monitor = BrowserSessionMonitor(server.shutdown)
    app.config["PROMPTLY_LIFECYCLE_TOKEN"] = lifecycle_token
    app.config["PROMPTLY_LIFECYCLE_HANDLER"] = monitor.notify
    monitor.start()

    browser_timer = threading.Timer(1.0, webbrowser.open, args=(url,))
    browser_timer.daemon = True
    browser_timer.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        browser_timer.cancel()
        monitor.stop()
        server.server_close()
        app.config.pop("PROMPTLY_LIFECYCLE_TOKEN", None)
        app.config.pop("PROMPTLY_LIFECYCLE_HANDLER", None)


if __name__ == "__main__":
    main()
