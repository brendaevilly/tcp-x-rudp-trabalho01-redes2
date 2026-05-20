#!/usr/bin/env python3
"""Gera arquivo de teste com tamanho configurável."""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=512_000, help="Tamanho em bytes")
    parser.add_argument("--name", default="testfile.bin")
    args = parser.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    path = DATA / args.name
    path.write_bytes(bytes([i % 256 for i in range(args.size)]))
    print(f"Gerado: {path} ({args.size} bytes)")


if __name__ == "__main__":
    main()
