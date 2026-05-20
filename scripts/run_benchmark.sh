#!/usr/bin/env bash
# Executa N rodadas TCP e R-UDP para cada cenário e grava métricas
# Uso: ./scripts/run_benchmark.sh [host] [runs]

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
export PYTHONPATH="${ROOT}"

HOST="${1:-127.0.0.1}"
RUNS="${2:-15}"
FILE="${ROOT}/data/testfile.bin"

if [[ ! -f "${FILE}" ]]; then
  python3 scripts/generate_test_file.py --size 512000
fi

echo "=== Benchmark: ${RUNS} execuções por modo/cenário em ${HOST} ==="

for SCENARIO in A B C; do
  for MODE in tcp rudp; do
    for ((i=1; i<=RUNS; i++)); do
      if [[ "${MODE}" == "tcp" ]]; then
        python3 src/tcp_client.py "${FILE}" --host "${HOST}" --scenario "${SCENARIO}" --run-id "${i}" || true
      else
        python3 src/rudp_client.py "${FILE}" --host "${HOST}" --scenario "${SCENARIO}" --run-id "${i}" || true
      fi
      sleep 0.2
    done
  done
done

echo "Logs em logs/transfers.jsonl"
python3 analysis/analyze.py
