"""
HTTP request handler for LoanFlow mock server.
"""

import json
from http.server import BaseHTTPRequestHandler

from mocks.risk_engine_scoring_logic import RiskEngineScoringLogic

# Module-level notification log — accessible from MockServerManager
notification_log = []


class MockRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler for mock endpoints."""

    server_version = "LoanFlowMock/1.0"

    def log_message(self, format, *args):
        """Silence default request logging during tests."""

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw_body = self.rfile.read(length).decode("utf-8")
        return json.loads(raw_body) if raw_body else {}

    def _write_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._write_json(200, {"status": "healthy"})
            return
        self._write_json(404, {"error_code": "NOT_FOUND", "message": "Not found"})

    def do_POST(self):
        if self.path == "/score":
            payload = self._read_json_body()
            score = RiskEngineScoringLogic.calculate_score(
                payload.get("annual_income", 0),
                payload.get("requested_amount", 0),
                payload.get("employment_status", ""),
            )
            decision = RiskEngineScoringLogic.get_decision(score)
            self._write_json(200, {"score": score, "decision": decision})
            return

        if self.path == "/notify":
            payload = self._read_json_body()
            notification_log.append(payload)
            self._write_json(200, {"status": "queued"})
            return

        self._write_json(404, {"error_code": "NOT_FOUND", "message": "Not found"})
