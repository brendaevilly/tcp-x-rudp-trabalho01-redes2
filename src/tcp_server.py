#!/usr/bin/env python3
"""Servidor TCP — recebe arquivo com cabeçalho X-Custom-Auth."""

from __future__ import annotations

import path_setup  # noqa: F401

import argparse
import socket
import sys
from pathlib import Path

from src.config import RECEIVED_DIR, TCP_PORT, custom_auth_hash

def recv_line(conn: socket.socket) -> str:
    buf = b""
    while b"\n" not in buf:
        chunk = conn.recv(1)
        if not chunk:
            break
        buf += chunk
    return buf.decode("utf-8", errors="replace").strip()

def handle_client(conn: socket.socket, addr: tuple[str, int]) -> None:
    auth_line = recv_line(conn)
    if not auth_line.startswith("X-Custom-Auth:"):
        print(f"[TCP] Auth ausente de {addr}", file=sys.stderr)
        conn.close()
        return
    token = auth_line.split(":", 1)[1].strip()
    if token != custom_auth_hash():
        print(f"[TCP] Auth inválido de {addr}", file=sys.stderr)
        conn.close()
        return

    meta = recv_line(conn)
    if not meta.startswith("FILE "):
        print(f"[TCP] Meta inválida: {meta}", file=sys.stderr)
        conn.close()
        return
    parts = meta.split()
    filename = parts[1]
    file_size = int(parts[2])
    dest = RECEIVED_DIR / f"tcp_{filename}"
    received = 0
    with dest.open("wb") as f:
        while received < file_size:
            chunk = conn.recv(min(65536, file_size - received))
            if not chunk:
                break
            f.write(chunk)
            received += len(chunk)
    conn.sendall(b"OK\n")
    print(f"[TCP] {addr} -> {dest} ({received}/{file_size} bytes)")
    
def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor TCP de transferência")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=TCP_PORT)
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((args.host, args.port))
    sock.listen(5)
    print(f"[TCP] Escutando em {args.host}:{args.port}")
    try:
        while True:
            conn, addr = sock.accept()
            handle_client(conn, addr)
    except KeyboardInterrupt:
        print("\n[TCP] Encerrando.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()