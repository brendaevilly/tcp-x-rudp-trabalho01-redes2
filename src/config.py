"""Configuração central: portas, chunk, autenticação X-Custom-Auth."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGS_DIR = ROOT / "logs"
RECEIVED_DIR = ROOT / "received"
DATA_DIR = ROOT / "data"
CAPTURES_DIR = ROOT / "captures"

for d in (LOGS_DIR, RECEIVED_DIR, DATA_DIR, CAPTURES_DIR):
    d.mkdir(parents=True, exist_ok=True)
    
def _load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())
        
_load_dotenv()

STUDENT_MATRICULA = os.environ.get("STUDENT_MATRICULA", "20249007096")
STUDENT_NOME = os.environ.get("STUDENT_NOME", "Brenda Evilly Oliveira de Moura")
TCP_PORT = int(os.environ.get("TCP_PORT", "5000"))
RUDP_PORT = int(os.environ.get("RUDP_PORT", "5001"))
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "1024"))
RUDP_TIMEOUT = float(os.environ.get("RUDP_TIMEOUT", "2.0"))
RUDP_MAX_RETRIES = int(os.environ.get("RUDP_MAX_RETRIES", "20"))

def custom_auth_hash() -> str:
    """SHA-256(Matrícula + Nome) em hexadecimal — campo X-Custom-Auth."""
    payload = f"{STUDENT_MATRICULA}{STUDENT_NOME}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def custom_auth_bytes() -> bytes:
    return bytes.fromhex(custom_auth_hash())