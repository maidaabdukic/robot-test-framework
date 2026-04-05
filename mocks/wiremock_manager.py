"""
Mock server manager for LoanFlow testing.
Manages the lifecycle of the local HTTP mock server.
"""

import threading
import time
from http.server import ThreadingHTTPServer

from mocks.mock_request_handler import MockRequestHandler


class WireMockManager:
    """Manages the local HTTP mock server for dependent services."""

    def __init__(self, port=9090):
        self.port = port
        self.server = None
        self._thread = None

    @property
    def is_running(self):
        """Return whether the mock server is currently running."""
        return self.server is not None

    def start(self):
        """Start mock server in a background thread."""
        if self.server is not None:
            return

        self.server = ThreadingHTTPServer(("127.0.0.1", self.port), MockRequestHandler)
        self._thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )
        self._thread.start()
        time.sleep(0.1)

    def stop(self):
        """Stop mock server."""
        if self.server is None:
            return

        self.server.shutdown()
        self.server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=1)
        self.server = None
        self._thread = None

    def reset(self):
        """Reset mock server by restarting it."""
        self.stop()
        self.start()


_server_instance = None


def start_mock_server(port=9090, debug=False):
    """Start the mock server."""
    del debug
    global _server_instance

    if _server_instance is None:
        _server_instance = WireMockManager(port=port)

    _server_instance.start()
    return _server_instance


def stop_mock_server():
    """Stop the mock server."""
    global _server_instance

    if _server_instance is not None:
        _server_instance.stop()
        _server_instance = None


if __name__ == "__main__":
    server = start_mock_server()
    try:
        print("Mock server started on port 9090")
        print("Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping mock server.")
        stop_mock_server()
