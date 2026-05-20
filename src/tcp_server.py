#!/usr/bin/env python3
"""Servidor R-UDP (Stop-and-Wait) — recebe arquivo com confiabilidade."""

from __future__ import annotations

import path_setup  # noqa: F401

import argparse
import socket
import sys
from pathlib import Path

from src.config import RECEIVED_DIR, RUDP_PORT
from src.rudp_protocol import MsgType, pack_packet, unpack_packet


class RudpServer:
    def __init__(self, host: str, port: int) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.client_addr: tuple[str, int] | None = None

    def send_ack(self, seq: int, ack: int) -> None:
        if self.client_addr is None:
            return
        pkt = pack_packet(MsgType.ACK, seq, ack)
        self.sock.sendto(pkt, self.client_addr)

    def recv_packet(self) -> tuple[MsgType, int, int, bytes]:
        while True:
            data, addr = self.sock.recvfrom(65535)
            try:
                mtype, seq, ack, payload, _ = unpack_packet(data)
                self.client_addr = addr
                return mtype, seq, ack, payload
            except ValueError as exc:
                print(f"[RUDP] Pacote inválido de {addr}: {exc}", file=sys.stderr)

    def wait_syn(self) -> tuple[str, int]:
        while True:
            mtype, _, _, payload = self.recv_packet()
            if mtype == MsgType.SYN:
                break
        meta = payload.decode("utf-8")
        parts = meta.split("|")
        if len(parts) != 2:
            raise ValueError(f"Meta SYN inválida: {meta}")
        filename, file_size_s = parts
        file_size = int(file_size_s)
        return filename, file_size

    def run(self) -> None:
        filename, file_size = self.wait_syn()
        expected_seq = 0
        self.send_ack(seq=0, ack=expected_seq)

        dest = RECEIVED_DIR / f"rudp_{filename}"
        received = 0
        with dest.open("wb") as f:
            while received < file_size:
                mtype, seq, _, payload = self.recv_packet()
                if mtype == MsgType.DATA:
                    if seq == expected_seq:
                        f.write(payload)
                        received += len(payload)
                        expected_seq = (expected_seq + 1) % (2**32)
                    self.send_ack(seq=0, ack=expected_seq)

        while True:
            mtype, _, _, _ = self.recv_packet()
            if mtype == MsgType.FIN:
                self.send_ack(seq=0, ack=expected_seq)
                break

        print(f"[RUDP] Salvo {dest} ({received}/{file_size} bytes)")

    def close(self) -> None:
        self.sock.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor R-UDP")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=RUDP_PORT)
    args = parser.parse_args()
    server = RudpServer(args.host, args.port)
    print(f"[RUDP] Escutando em {args.host}:{args.port}")
    try:
        while True:
            server.run()
    except KeyboardInterrupt:
        print("\n[RUDP] Encerrando.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
