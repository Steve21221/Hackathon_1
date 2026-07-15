"""Start Promptly locally and open it in the user's default browser."""

import threading
import webbrowser

from app import app


if __name__ == "__main__":
    threading.Timer(1.25, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
