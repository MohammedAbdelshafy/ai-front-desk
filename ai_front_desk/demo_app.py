"""Loopback-only HTTP demo for the synthetic dental intake workflow.

Run with: python -m ai_front_desk.demo_app
Never expose this demo server to a network or use it with real patient data.
"""
from __future__ import annotations

import json
import mimetypes
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from ai_front_desk.clinical_intake import (
    IntakeNotFoundError,
    IntakeValidationError,
    create_intake,
    get_intake,
    initialize_database,
    list_intakes,
    review_intake,
    seed_demo_records,
)

MAX_BODY_BYTES = 32 * 1024
LOCAL_HOST = "127.0.0.1"
_ID_RE = re.compile(r"[a-f0-9]{32}\Z")
_STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}


def default_database_path() -> Path:
    configured = os.environ.get("DENTAL_DEMO_DB", "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".ai-front-desk" / "dental-demo.sqlite3"


def make_handler(db_path: str | Path):
    static_dir = Path(__file__).with_name("static")

    class DemoHandler(BaseHTTPRequestHandler):
        server_version = "MiaDentalDemo/0.1"
        sys_version = ""

        def log_message(self, fmt: str, *args: object) -> None:
            # Avoid logging request data; standard paths contain only fixed routes or opaque IDs.
            super().log_message(fmt, *args)

        def _headers(self, content_type: str, length: int) -> None:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(length))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; base-uri 'none'; object-src 'none'; "
                "form-action 'self'; frame-ancestors 'none'; script-src 'self'; "
                "style-src 'self'; img-src 'self' data: https://mohammedabdelshafy.github.io; "
                "connect-src 'self'",
            )

        def _send_bytes(self, status: int, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; base-uri 'none'; object-src 'none'; "
                "form-action 'self'; frame-ancestors 'none'; script-src 'self'; "
                "style-src 'self'; img-src 'self' data: https://mohammedabdelshafy.github.io; "
                "connect-src 'self'",
            )
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, data: object) -> None:
            body = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def _body_json(self) -> dict:
            raw_length = self.headers.get("Content-Length", "")
            try:
                length = int(raw_length)
            except (TypeError, ValueError):
                raise IntakeValidationError("A valid Content-Length header is required.")
            if length < 0 or length > MAX_BODY_BYTES:
                raise IntakeValidationError("Request body is too large.")
            if self.headers.get_content_type() != "application/json":
                raise IntakeValidationError("Send JSON using Content-Type: application/json.")
            raw = self.rfile.read(length)
            try:
                obj = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise IntakeValidationError("Request body must be valid UTF-8 JSON.")
            if not isinstance(obj, dict):
                raise IntakeValidationError("Request body must be a JSON object.")
            return obj

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path in _STATIC_FILES:
                filename, content_type = _STATIC_FILES[path]
                try:
                    body = (static_dir / filename).read_bytes()
                except OSError:
                    self._json(500, {"error": "Demo asset is unavailable."})
                    return
                self._send_bytes(200, content_type, body)
                return
            if path == "/api/health":
                self._json(200, {
                    "ok": True,
                    "app": "Mia Dental Intake Demo",
                    "mode": "synthetic-demo-only",
                    "database_scope": "local-user-machine",
                    "external_messaging_enabled": False,
                    "booking_enabled": False,
                    "clinical_decision_support_enabled": False,
                    "real_patient_data_allowed": False,
                })
                return
            if path == "/api/intakes":
                try:
                    self._json(200, {"items": list_intakes(db_path)})
                except Exception:
                    self._json(500, {"error": "Could not load demo intake records."})
                return
            prefix = "/api/intakes/"
            if path.startswith(prefix):
                intake_id = path[len(prefix):]
                if not _ID_RE.fullmatch(intake_id):
                    self._json(400, {"error": "Invalid demo intake identifier."})
                    return
                try:
                    self._json(200, get_intake(db_path, intake_id))
                except IntakeNotFoundError:
                    self._json(404, {"error": "Demo intake was not found."})
                except Exception:
                    self._json(500, {"error": "Could not load demo intake."})
                return
            self._json(404, {"error": "Not found."})

        def do_POST(self) -> None:
            path = urlsplit(self.path).path
            try:
                payload = self._body_json()
                if path == "/api/intakes":
                    result = create_intake(db_path, payload)
                    self._json(201, result)
                    return

                match = re.fullmatch(r"/api/intakes/([a-f0-9]{32})/review", path)
                if match:
                    allowed = {"reviewer", "outcome", "notes"}
                    extra = set(payload) - allowed
                    if extra:
                        raise IntakeValidationError("Unexpected review field: " + sorted(extra)[0])
                    result = review_intake(
                        db_path,
                        match.group(1),
                        payload.get("reviewer"),
                        payload.get("outcome"),
                        payload.get("notes", ""),
                    )
                    self._json(200, result)
                    return
                self._json(404, {"error": "Not found."})
            except IntakeValidationError as exc:
                self._json(400, {"error": str(exc)})
            except IntakeNotFoundError:
                self._json(404, {"error": "Demo intake was not found."})
            except Exception:
                # Do not return database details, payloads or stack traces to the browser.
                self._json(500, {"error": "The demo could not save this action. Try again."})

        def do_PUT(self) -> None:
            self._json(405, {"error": "Method not allowed."})

        def do_DELETE(self) -> None:
            self._json(405, {"error": "Delete is not available in this demo."})

    return DemoHandler


def make_server(db_path: str | Path | None = None, host: str = LOCAL_HOST, port: int = 8765):
    if host != LOCAL_HOST:
        raise ValueError("This prototype must bind to 127.0.0.1 only.")
    database = Path(db_path) if db_path is not None else default_database_path()
    initialize_database(database)
    return ThreadingHTTPServer((LOCAL_HOST, int(port)), make_handler(database))


def main() -> None:
    database = default_database_path()
    initialize_database(database)
    seed_demo_records(database)
    server = make_server(database, host=LOCAL_HOST, port=int(os.environ.get("PORT", "8765")))
    print("Mia Dental Intake Demo is available at http://127.0.0.1:" + str(server.server_port))
    print("DEMO ONLY: use fictional data. Never enter real patient information.")
    print("External messaging, booking, and clinical decision support are disabled.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping the local demo.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
