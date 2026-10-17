#!/usr/bin/env python3
"""Create local Compose credentials without displaying or overwriting them."""
import base64
import os
from pathlib import Path
import secrets

root = Path(__file__).resolve().parent.parent
target = root / ".env"
content = (
    f"DB_PASSWORD={secrets.token_hex(32)}\n"
    f"MYSQL_ROOT_PASSWORD={secrets.token_hex(32)}\n"
    f"JWT_SECRET={base64.b64encode(secrets.token_bytes(32)).decode()}\n"
    "APP_PORT=8000\nADMINER_PORT=8080\n"
)
try:
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    raise SystemExit(".env already exists; preserved existing credentials.")
with os.fdopen(fd, "w") as stream:
    stream.write(content)
print("Created private .env with fresh credentials. Keep it out of Git.")
