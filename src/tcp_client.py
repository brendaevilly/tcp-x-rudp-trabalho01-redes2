#!/usr/bin/env python3
"""Cliente TCP — envia arquivo e registra métricas."""

from __future__ import annotations

import path_setup  # noqa: F401

import argparse
import socket
import sys
import time
from pathlib import Path

from src.config import TCP_PORT, custom_auth_hash
from src.metrics import MetricsLogger, TransferMetrics

def send_file(host: str, port: int, file_path: Path, scenario: str, run_id: int) -> TransferMetrics:
    data = file_path.read_bytes()
    file_size = len(data)
    start = time.perf_counter()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    header = (
        f"X-Custom-Auth: {custom_auth_hash()}\n"
        f"FILE {file_path.name} {file_size}\n"
    )
    sock.sendall(header.encode("utf-8"))
    offset = 0
    while offset < file_size:
        sent = sock.send(data[offset : offset + 65536])
        if sent == 0:
            raise RuntimeError("Conexão fechada durante envio")
        offset += sent
    resp = b""
    while b"\n" not in resp:
        resp += sock.recv(1)
    sock.close()
    duration = time.perf_counter() - start
    metrics = TransferMetrics(
        mode="tcp",
        scenario=scenario,
        run_id=run_id,
        bytes_sent=file_size,
        duration_s=duration,
        throughput_bps=0.0,
        host=host,
        file_name=file_path.name,
    )
    return metrics

def main() -> None:
    parser = argparse.ArgumentParser(description="Cliente TCP de transferência")
    parser.add_argument("file", type=Path, help="Arquivo a enviar")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=TCP_PORT)
    parser.add_argument("--scenario", default="local", choices=["A", "B", "C", "local"])
    parser.add_argument("--run-id", type=int, default=1)
    parser.add_argument("--no-log", action="store_true")
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"Arquivo não encontrado: {args.file}", file=sys.stderr)
        sys.exit(1)

    metrics = send_file(args.host, args.port, args.file, args.scenario, args.run_id)
    print(
        f"[TCP] {metrics.bytes_sent} bytes em {metrics.duration_s:.4f}s "
        f"-> {metrics.throughput_mbps():.2f} Mbps"
    )
    if not args.no_log:
        MetricsLogger().log(metrics)


if __name__ == "__main__":
    main()
