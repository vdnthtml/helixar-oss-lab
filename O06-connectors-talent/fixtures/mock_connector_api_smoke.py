#!/usr/bin/env python3
"""Loopback-only synthetic connector contract fixture with isolated fake tokens."""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import cast
from urllib.parse import parse_qs, urlparse

LAB = Path(__file__).resolve().parents[1]
TOKEN_TENANT = {
    "Synthetic token-a.invalid": "tenant-a.invalid",
    "Synthetic token-b.invalid": "tenant-b.invalid",
}
contacts: dict[str, dict[str, dict[str, str]]] = {tenant: {} for tenant in TOKEN_TENANT.values()}
suppressed: dict[str, set[str]] = {tenant: set() for tenant in TOKEN_TENANT.values()}
request_count = 0


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return

    def reply(self, status: int, body: object) -> None:
        payload = json.dumps(body, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def tenant(self) -> str | None:
        return TOKEN_TENANT.get(self.headers.get("Authorization", ""))

    def body(self) -> dict[str, str]:
        size = int(self.headers.get("Content-Length", "0"))
        data = bytes(self.rfile.read(size))
        return json.loads(data or b"{}")

    def do_GET(self) -> None:
        global request_count
        request_count += 1
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.reply(200, {"status": "ok", "bind": self.server.server_address[0]})
            return
        tenant = self.tenant()
        requested = parse_qs(parsed.query).get("tenant", [""])[0]
        if parsed.path == "/export" and tenant and tenant == requested:
            self.reply(200, {"tenant": tenant, "contacts": list(contacts[tenant].values())})
            return
        self.reply(403, {"error": "tenant isolation"})

    def do_POST(self) -> None:
        global request_count
        request_count += 1
        tenant = self.tenant()
        body = self.body()
        if not tenant or body.get("tenant_id") != tenant:
            self.reply(403, {"error": "tenant isolation"})
            return
        if self.path == "/suppression":
            suppressed[tenant].add(body["email"])
            self.reply(201, {"suppressed": True})
            return
        if self.path == "/contacts":
            if body["email"] in suppressed[tenant]:
                self.reply(409, {"error": "suppressed identity"})
                return
            external_id = body["external_id"]
            contacts[tenant][external_id] = body
            self.reply(201, {"external_id": external_id})
            return
        self.reply(404, {"error": "not found"})

    def do_DELETE(self) -> None:
        global request_count
        request_count += 1
        tenant = self.tenant()
        external_id = self.path.removeprefix("/contacts/")
        if not tenant or self.path == external_id:
            self.reply(403, {"error": "tenant isolation"})
            return
        contacts[tenant].pop(external_id, None)
        self.reply(200, {"deleted": external_id})


def request(base: str, method: str, path: str, token: str = "", body: dict[str, str] | None = None) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = token
    req = urllib.request.Request(
        base + path,
        method=method,
        headers=headers,
        data=json.dumps(body).encode() if body is not None else None,
    )
    try:
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
host, port = cast(tuple[str, int], server.server_address)
base = f"http://{host}:{port}"
try:
    assert request(base, "GET", "/health") == (200, {"bind": "127.0.0.1", "status": "ok"})
    token_a = "Synthetic token-a.invalid"
    token_b = "Synthetic token-b.invalid"
    a = {"tenant_id": "tenant-a.invalid", "external_id": "a-1", "email": "alice@tenant-a.invalid"}
    b = {"tenant_id": "tenant-b.invalid", "external_id": "b-1", "email": "bob@tenant-b.invalid"}
    assert request(base, "POST", "/contacts", token_a, a)[0] == 201
    assert request(base, "POST", "/contacts", token_a, b)[0] == 403
    assert request(base, "POST", "/contacts", token_b, b)[0] == 201
    exported = request(base, "GET", "/export?tenant=tenant-a.invalid", token_a)
    assert exported[0] == 200 and [item["external_id"] for item in exported[1]["contacts"]] == ["a-1"]
    assert request(base, "GET", "/export?tenant=tenant-b.invalid", token_a)[0] == 403
    assert request(base, "DELETE", "/contacts/a-1", token_a)[0] == 200
    assert request(base, "GET", "/export?tenant=tenant-a.invalid", token_a)[1]["contacts"] == []
    suppression = {"tenant_id": "tenant-a.invalid", "email": "suppressed@tenant-a.invalid"}
    assert request(base, "POST", "/suppression", token_a, suppression)[0] == 201
    suppressed_contact = {**suppression, "external_id": "a-2"}
    assert request(base, "POST", "/contacts", token_a, suppressed_contact)[0] == 409
    result = {
        "status": "PASS",
        "bind": host,
        "port": port,
        "healthCheck": "PASS",
        "syntheticTokens": 2,
        "realTokens": 0,
        "tenantIsolation": "PASS",
        "crossTenantDenied": "PASS",
        "export": "PASS",
        "deletion": "PASS",
        "suppression": "PASS",
        "loopbackRequests": request_count,
        "externalRequests": 0,
    }
    (LAB / "artifacts" / "mock-connector-contract.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)
