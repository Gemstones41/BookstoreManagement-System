#!/usr/bin/env python3
"""Exercise the real API. State files contain temporary test credentials: do not commit."""
import argparse
import json
import os
from pathlib import Path
import secrets
import urllib.error
import urllib.request
import uuid

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--url", default="http://127.0.0.1:8000")
parser.add_argument("--state", type=Path, required=True)
parser.add_argument("--verify-persistence", action="store_true")
args = parser.parse_args()

def request(method, path, body=None, token=None):
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(args.url.rstrip("/") + path, data, headers, method=method)
    try:
        response = urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        status = response.status
        payload = response.read()
    try:
        payload = json.loads(payload) if payload else None
    except ValueError:
        payload = None
    return status, payload

def expect(condition, message):
    if not condition:
        raise SystemExit("FAIL: " + message)
    print("PASS: " + message)

status, health = request("GET", "/actuator/health")
expect(status == 200 and health.get("status") == "UP", "application and database health")

if args.verify_persistence:
    state = json.loads(args.state.read_text())
    status, book = request("GET", f"/books/{state['book_id']}", token=state["token"])
    expect(status == 200 and book and book["isbn"] == state["isbn"],
           "saved book and original JWT survive container recreation")
    status, login = request("POST", "/customers/login", {
        "email": state["email"], "password": state["password"]})
    expect(status == 200 and bool(login.get("token")), "customer and password survive recreation")
    status, _ = request("DELETE", f"/books/{state['book_id']}", token=state["token"])
    expect(200 <= status < 300, "test book cleanup")
    status, _ = request("DELETE", f"/customers/{state['customer_id']}", token=state["token"])
    expect(200 <= status < 300, "test customer cleanup")
    args.state.unlink()
    raise SystemExit(0)

expect(not args.state.exists(), "state file will not overwrite previous test credentials")
state = {"email": f"docker-smoke-{uuid.uuid4().hex}@example.invalid",
         "password": secrets.token_urlsafe(24), "isbn": "smoke-" + uuid.uuid4().hex[:20]}
status, customer = request("POST", "/customers/register", {
    "firstName": "Docker", "lastName": "Smoke", "email": state["email"],
    "password": state["password"], "phoneNumber": "0000000000"})
expect(200 <= status < 300 and customer and customer.get("id"), "register real customer")
expect("password" not in customer, "registration response does not expose password hash")
state["customer_id"] = customer["id"]
status, login = request("POST", "/customers/login", {
    "email": state["email"], "password": state["password"]})
expect(status == 200 and bool(login.get("token")), "login with real password verification")
state["token"] = login["token"]
status, invalid_login = request("POST", "/customers/login", {
    "email": state["email"], "password": "wrong-" + secrets.token_urlsafe(16)})
expect(status >= 400 and not (invalid_login or {}).get("token"), "incorrect password issues no token")
if status not in (400, 401, 403):
    print(f"KNOWN APPLICATION ISSUE: incorrect-password response is HTTP {status}; should be 401.")
status, _ = request("GET", "/books")
expect(status in (401, 403), "anonymous request cannot access books")
status, _ = request("GET", "/books", token="invalid-token")
expect(status in (401, 403), "invalid JWT cannot access books")
status, _ = request("GET", "/admin", token=state["token"])
expect(status == 403, "customer token cannot access admin endpoint")

book = {"title": "Docker verification book", "isbn": state["isbn"],
        "price": 12.5, "stockQuantity": 4, "language": "English"}
status, created = request("POST", "/books", book, state["token"])
expect(200 <= status < 300 and created and created.get("id"), "create book in MySQL")
state["book_id"] = created["id"]
book.update(title="Docker verification updated", stockQuantity=7)
status, updated = request("PUT", f"/books/{state['book_id']}", book, state["token"])
expect(status == 200 and updated["title"] == book["title"] and updated["quantity"] == 7,
       "update book and stock")
status, books = request("GET", "/books/search/isbn/" + state["isbn"], token=state["token"])
expect(status == 200 and any(b["id"] == state["book_id"] for b in books), "search stored book")
args.state.parent.mkdir(parents=True, exist_ok=True)
fd = os.open(args.state, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w") as stream:
    json.dump(state, stream)
print("Saved private fixture state. Recreate containers without deleting volumes, then run --verify-persistence.")
