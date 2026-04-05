"""
Robot Framework keyword library — mock server lifecycle management.
"""

import threading
import time
import requests

from mocks.wiremock_manager import start_mock_server, stop_mock_server
from mocks.application_api_mock import app as api_app, reset_database
from mocks.mock_request_handler import notification_log

"""Manages mock server lifecycle for Robot Framework test suites."""


class MockServerManager:
    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self):
        self._api_thread = None
        self._api_server = None

    def _wait_for_health(self, url, expected_up=True, timeout=3.0, interval=0.1):
        """Wait until a service becomes healthy or unavailable."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                response = requests.get(url, timeout=0.2)
                is_up = response.status_code == 200
            except Exception:
                is_up = False

            if is_up == expected_up:
                return

            time.sleep(interval)

        state = "healthy" if expected_up else "unavailable"
        raise AssertionError(
            f"Service at {url} did not become {state} within {timeout} seconds."
        )

    """Start Risk Engine mock (port 9090) and Application API mock (port 8000)."""

    def start_mock_servers(self):
        reset_database()
        notification_log.clear()
        start_mock_server(port=9090)
        self._wait_for_health("http://127.0.0.1:9090/health", expected_up=True)

        def _run_api():
            import uvicorn

            config = uvicorn.Config(
                api_app,
                host="127.0.0.1",
                port=8000,
                log_level="warning",
            )
            self._api_server = uvicorn.Server(config)
            self._api_server.run()

        if self._api_thread is None or not self._api_thread.is_alive():
            self._api_thread = threading.Thread(target=_run_api, daemon=True)
            self._api_thread.start()
        self._wait_for_health("http://127.0.0.1:8000/health", expected_up=True)

    def stop_mock_servers(self):
        """Stop both the Risk Engine mock and the Application API mock."""
        stop_mock_server()
        self._wait_for_health("http://127.0.0.1:9090/health", expected_up=False)

        if self._api_server is not None:
            self._api_server.should_exit = True

        if self._api_thread is not None and self._api_thread.is_alive():
            self._api_thread.join(timeout=3)

        self._api_server = None
        self._api_thread = None
        reset_database()
        notification_log.clear()
        self._wait_for_health("http://127.0.0.1:8000/health", expected_up=False)

    """Stop only the Risk Engine mock (port 9090) while Application API stays running."""

    def stop_risk_engine(self):
        stop_mock_server()
        self._wait_for_health("http://127.0.0.1:9090/health", expected_up=False)

    """Restart the Risk Engine mock (port 9090)."""

    def start_risk_engine(self):
        start_mock_server(port=9090)
        self._wait_for_health("http://127.0.0.1:9090/health", expected_up=True)

    """Clear all applications from in-memory store."""

    def reset_application_database(self):
        reset_database()

    def reset_mock_state(self):
        """Clear in-memory applications and notification history."""
        reset_database()
        notification_log.clear()

    """Get list of notifications sent to the Notification Service mock."""

    def get_notification_log(self):
        return list(notification_log)

    def wait_for_notification(self, application_id, timeout=3.0, interval=0.1):
        """Wait until a notification for the given application ID is received."""
        deadline = time.time() + timeout

        while time.time() < deadline:
            for notification in notification_log:
                if notification.get("application_id") == application_id:
                    return notification

            time.sleep(interval)

        raise AssertionError(
            f"Notification for application {application_id} was not received within {timeout} seconds."
        )

    """Clear the notification log."""

    def clear_notification_log(self):
        notification_log.clear()
