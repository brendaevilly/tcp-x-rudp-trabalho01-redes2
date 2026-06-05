#!/usr/bin/env bash
# Sobe containers, aplica tc no cliente por cenário e roda benchmark
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "${ROOT}"

docker compose build --no-cache
docker compose up -d server
sleep 2
docker compose up -d client
sleep 2

SERVER_IP="172.28.0.10"
CLIENT_CONTAINER="redes2-client"

# Limpa log anterior para não misturar runs de sessões diferentes
docker exec "${CLIENT_CONTAINER}" bash -c "truncate -s 0 /app/logs/transfers.jsonl 2>/dev/null || true"

for SCENARIO in A B C; do
  echo ">>> Aplicando cenário ${SCENARIO} no cliente"
  docker exec "${CLIENT_CONTAINER}" bash /app/scripts/setup_tc.sh "${SCENARIO}" eth0
  docker exec -e PYTHONPATH=/app "${CLIENT_CONTAINER}" \
    bash /app/scripts/run_benchmark.sh "${SERVER_IP}" 10 "${SCENARIO}"
done

docker exec "${CLIENT_CONTAINER}" bash /app/scripts/setup_tc.sh clear eth0

# Gera gráficos e CSV a partir dos logs acumulados dos 3 cenários
docker exec -e PYTHONPATH=/app "${CLIENT_CONTAINER}" python3 /app/analysis/analyze.py

echo "Gráficos e CSV em /app/analysis/output"
echo "Testes Docker concluídos. Logs em logs/transfers.jsonl"
