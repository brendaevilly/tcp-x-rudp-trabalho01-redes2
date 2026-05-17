"""Registro de métricas de transferência (tempo, throughput, retransmissões)."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.config import LOGS_DIR

@dataclass
class TransferMetrics:
    mode: str  # tcp | rudp
    scenario: str  # A | B | C | local
    run_id: int
    bytes_sent: int
    duration_s: float
    throughput_bps: float
    retransmissions: int = 0
    host: str = "127.0.0.1"
    file_name: str = ""
    timestamp: float = 0.0
    
    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        if self.duration_s > 0:
            self.throughput_bps = self.bytes_sent * 8 / self.duration_s
        else:
            self.throughput_bps = 0.0

    def throughput_mbps(self) -> float:
        return self.throughput_bps / 1_000_000
    
class MetricsLogger:
    def __init__(self, log_file: Path | None = None) -> None:
        self.log_file = log_file or (LOGS_DIR / "transfers.jsonl")

    def log(self, metrics: TransferMetrics) -> None:
        record = asdict(metrics)
        record["throughput_mbps"] = metrics.throughput_mbps()
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            
    @staticmethod
    def load_all(path: Path | None = None) -> list[dict[str, Any]]:
        log_path = path or (LOGS_DIR / "transfers.jsonl")
        if not log_path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
        return rows