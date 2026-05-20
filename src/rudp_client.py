#!/usr/bin/env python3
"""Cliente R-UDP (Stop-and-Wait) — timeout, retransmissão e métricas."""

from __future__ import annotations

import argparse
import socket
import sys
import time
from pathlib import Path

from src.config import RUDP_MAX_RETRIES, RUDP_PORT, RUDP_TIMEOUT
from src.metrics import MetricsLogger, TransferMetrics
from src.rudp_protocol import MsgType, max_payload_size, pack_packet, unpack_packet


class RudpClient:
    def __init__(self, host: str, port: int, timeout: float) -> None:
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(timeout)
        self.retransmissions = 0

    def send_wait_ack(
        self,
        pkt: bytes,
        expected_ack: int,
        max_retries: int,
    ) -> None:
        for attempt in range(max_retries):
            self.sock.sendto(pkt, (self.host, self.port))
            try:
                data, _ = self.sock.recvfrom(65535)
                mtype, _, ack, _, _ = unpack_packet(data)
                if mtype == MsgType.ACK and ack == expected_ack:
                    return
            except socket.timeout:
                if attempt > 0:
                    self.retransmissions += 1
                continue
            except ValueError:
                continue
        raise TimeoutError(f"Sem ACK para seq esperado ack={expected_ack}")

    def send_file(
        self,
        file_path: Path,
        scenario: str,
        run_id: int,
    ) -> TransferMetrics:
        data = file_path.read_bytes()
        file_size = len(data)
        chunk = max_payload_size()
        start = time.perf_counter()

        syn_payload = f"{file_path.name}|{file_size}".encode("utf-8")
        syn_pkt = pack_packet(MsgType.SYN, seq=0, ack=0, payload=syn_payload)
        self.send_wait_ack(syn_pkt, expected_ack=0, max_retries=RUDP_MAX_RETRIES)

        seq = 0
        offset = 0
        while offset < file_size:
            piece = data[offset : offset + chunk]
            pkt = pack_packet(MsgType.DATA, seq=seq, ack=0, payload=piece)
            next_ack = (seq + 1) % (2**32)
            self.send_wait_ack(pkt, expected_ack=next_ack, max_retries=RUDP_MAX_RETRIES)
            offset += len(piece)
            seq = next_ack

        fin_pkt = pack_packet(MsgType.FIN, seq=seq, ack=0, payload=b"")
        self.send_wait_ack(fin_pkt, expected_ack=seq, max_retries=RUDP_MAX_RETRIES)

        duration = time.perf_counter() - start
        return TransferMetrics(
            mode="rudp",
            scenario=scenario,
            run_id=run_id,
            bytes_sent=file_size,
            duration_s=duration,
            throughput_bps=0.0,
            retransmissions=self.retransmissions,
            host=self.host,
            file_name=file_path.name,
        )

    def close(self) -> None:
        self.sock.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Cliente R-UDP")
    parser.add_argument("file", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=RUDP_PORT)
    parser.add_argument("--timeout", type=float, default=RUDP_TIMEOUT)
    parser.add_argument("--scenario", default="local", choices=["A", "B", "C", "local"])
    parser.add_argument("--run-id", type=int, default=1)
    parser.add_argument("--no-log", action="store_true")
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"Arquivo não encontrado: {args.file}", file=sys.stderr)
        sys.exit(1)

    client = RudpClient(args.host, args.port, args.timeout)
    try:
        metrics = client.send_file(args.file, args.scenario, args.run_id)
        print(
            f"[RUDP] {metrics.bytes_sent} bytes em {metrics.duration_s:.4f}s "
            f"-> {metrics.throughput_mbps():.2f} Mbps "
            f"(retrans: {metrics.retransmissions})"
        )
        if not args.no_log:
            MetricsLogger().log(metrics)
    finally:
        client.close()


if __name__ == "__main__":
    main()
