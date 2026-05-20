#!/usr/bin/env python3
"""
Exporta estatísticas de um .pcap para CSV (validação cruzada com a aplicação).
Requer tshark instalado: sudo apt install tshark
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path


def export_pcap(pcap: Path, out_csv: Path) -> None:
    cmd = [
        "tshark",
        "-r",
        str(pcap),
        "-T",
        "fields",
        "-E",
        "header=y",
        "-E",
        "separator=,",
        "-e",
        "frame.number",
        "-e",
        "frame.time_relative",
        "-e",
        "ip.src",
        "-e",
        "ip.dst",
        "-e",
        "tcp.len",
        "-e",
        "udp.length",
        "-e",
        "data.data",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print("Erro ao executar tshark. Instale com: sudo apt install tshark", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    lines = result.stdout.strip().splitlines()
    if not lines:
        print("Nenhum pacote no pcap.", file=sys.stderr)
        sys.exit(1)

    reader = csv.reader(lines)
    rows = list(reader)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    # Resumo para validação cruzada
    summary_path = out_csv.with_name(out_csv.stem + "_summary.txt")
    tcp_bytes = 0
    udp_bytes = 0
    for row in rows[1:]:
        if len(row) < 8:
            continue
        tcp_len, udp_len = row[5], row[6]
        if tcp_len:
            tcp_bytes += int(tcp_len)
        if udp_len:
            udp_bytes += int(udp_len)
    summary = (
        f"Pacotes (sem cabeçalho): {len(rows) - 1}\n"
        f"Bytes payload TCP (tcp.len): {tcp_bytes}\n"
        f"Bytes UDP incl. cabeçalho UDP (udp.length): {udp_bytes}\n"
        f"Tempo relativo máximo: consulte coluna frame.time_relative no CSV\n"
    )
    summary_path.write_text(summary, encoding="utf-8")
    print(summary)
    print(f"CSV: {out_csv}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta pcap para CSV via tshark")
    parser.add_argument("pcap", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()
    out = args.output or args.pcap.with_suffix(".csv")
    export_pcap(args.pcap, out)


if __name__ == "__main__":
    main()
