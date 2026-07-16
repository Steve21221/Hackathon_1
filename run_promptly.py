"""Start Promptly locally and open it in the user's default browser."""

from __future__ import annotations

import os
import socket
import threading
import webbrowser

from app import app


HOST = "127.0.0.1"
DEFAULT_PORT = 5000
PORT_ATTEMPTS = 20


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
    print("Keep this window open while you use Promptly. Press Ctrl+C to stop it.")

    browser_timer = threading.Timer(1.0, webbrowser.open, args=(url,))
    browser_timer.daemon = True
    browser_timer.start()
    app.run(host=HOST, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
