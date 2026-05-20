#!/usr/bin/env bash
# Captura tráfego com tcpdump durante os testes
# Uso: ./scripts/capture_traffic.sh [interface] [nome_base]

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IFACE="${1:-any}"
BASE="${2:-capture}"
OUT="${ROOT}/captures/${BASE}_$(date +%Y%m%d_%H%M%S).pcap"
mkdir -p "${ROOT}/captures"

echo "Capturando em ${IFACE} -> ${OUT}"
echo "Pressione Ctrl+C para parar."
sudo tcpdump -i "${IFACE}" -w "${OUT}" 'udp port 5001 or tcp port 5000'
