#!/usr/bin/env python3
"""
Análise estatística: vazão mín/média/máx e desvio padrão.
Gera gráficos comparando TCP vs R-UDP por cenário.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import pandas as pd

from src.config import LOGS_DIR
from src.metrics import MetricsLogger

OUTPUT = ROOT / "analysis" / "output"


def load_dataframe() -> pd.DataFrame:
    rows = MetricsLogger.load_all()
    if not rows:
        raise SystemExit("Nenhum dado em logs/transfers.jsonl. Execute os testes primeiro.")
    df = pd.DataFrame(rows)
    if "throughput_mbps" not in df.columns:
        df["throughput_mbps"] = df["throughput_bps"] / 1_000_000
    return df


def summary_table(df: pd.DataFrame) -> pd.DataFrame:
    agg = (
        df.groupby(["scenario", "mode"])["throughput_mbps"]
        .agg(["min", "mean", "max", "std", "count"])
        .reset_index()
    )
    agg.columns = [
        "cenario",
        "modo",
        "vazao_min_mbps",
        "vazao_media_mbps",
        "vazao_max_mbps",
        "desvio_padrao_mbps",
        "amostras",
    ]
    return agg


def plot_throughput_bars(df: pd.DataFrame, out_dir: Path) -> None:
    summary = summary_table(df)
    scenarios = sorted(df["scenario"].unique())
    modes = ["tcp", "rudp"]
    x = range(len(scenarios))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    for i, mode in enumerate(modes):
        means = []
        stds = []
        for sc in scenarios:
            row = summary[(summary["cenario"] == sc) & (summary["modo"] == mode)]
            means.append(row["vazao_media_mbps"].iloc[0] if len(row) else 0)
            stds.append(row["desvio_padrao_mbps"].iloc[0] if len(row) else 0)
        offset = [xi + (i - 0.5) * width for xi in x]
        ax.bar(offset, means, width, yerr=stds, capsize=4, label=mode.upper())

    ax.set_xticks(list(x))
    ax.set_xticklabels([f"Cenário {s}" for s in scenarios])
    ax.set_ylabel("Throughput médio (Mbps)")
    ax.set_title("TCP vs R-UDP — média e desvio padrão")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "throughput_comparison.png", dpi=150)
    plt.close(fig)


def plot_duration_box(df: pd.DataFrame, out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    df_plot = df.copy()
    df_plot["label"] = df_plot["mode"].str.upper() + " / " + df_plot["scenario"]
    df_plot.boxplot(column="duration_s", by="label", ax=ax, rot=45)
    ax.set_title("Tempo de transferência por modo e cenário")
    ax.set_ylabel("Duração (s)")
    fig.suptitle("")
    fig.tight_layout()
    fig.savefig(out_dir / "duration_boxplot.png", dpi=150)
    plt.close(fig)


def plot_retransmissions(df: pd.DataFrame, out_dir: Path) -> None:
    rudp = df[df["mode"] == "rudp"]
    if rudp.empty or rudp["retransmissions"].sum() == 0:
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    rudp.groupby("scenario")["retransmissions"].mean().plot(kind="bar", ax=ax, color="coral")
    ax.set_title("Retransmissões médias (R-UDP)")
    ax.set_ylabel("Retransmissões")
    ax.set_xlabel("Cenário")
    fig.tight_layout()
    fig.savefig(out_dir / "rudp_retransmissions.png", dpi=150)
    plt.close(fig)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    df = load_dataframe()
    summary = summary_table(df)
    summary.to_csv(OUTPUT / "summary_statistics.csv", index=False)
    print(summary.to_string(index=False))

    plot_throughput_bars(df, OUTPUT)
    plot_duration_box(df, OUTPUT)
    plot_retransmissions(df, OUTPUT)
    print(f"\nGráficos e CSV em {OUTPUT}")


if __name__ == "__main__":
    main()
