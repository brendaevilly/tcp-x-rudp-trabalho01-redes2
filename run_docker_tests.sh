#!/usr/bin/env bash
# Sobe containers, aplica tc no cliente e roda benchmark
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}/docker"

docker compose build
docker compose up -d server
sleep 2
docker compose up -d client
sleep 2

SERVER_IP="172.28.0.10"
CLIENT_CONTAINER="redes2-client"

for SCENARIO in A B C; do
  echo ">>> Aplicando cenário ${SCENARIO} no cliente"
  docker exec "${CLIENT_CONTAINER}" bash /app/scripts/setup_tc.sh "${SCENARIO}" eth0
  docker exec -e PYTHONPATH=/app "${CLIENT_CONTAINER}" \
    bash /app/scripts/run_benchmark.sh "${SERVER_IP}" 10
done

docker exec "${CLIENT_CONTAINER}" bash /app/scripts/setup_tc.sh clear eth0
echo "Testes Docker concluídos. Logs em logs/transfers.jsonl"
