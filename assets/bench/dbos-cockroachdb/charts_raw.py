"""
charts_raw.py: raw-write fact-check charts.
1. Raw writes/s — PG vs CRDB side by side
2. Four-number summary bar: raw PG / raw CRDB / workflow PG / workflow CRDB at saturation
"""
import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

BLOG_ROOT = "/Users/elkouhen/Hackathon-RoboCrab/aelkouhen.github.io"
ASSET_DIR = f"{BLOG_ROOT}/assets/bench/dbos-cockroachdb"

import os
os.makedirs(ASSET_DIR, exist_ok=True)

with open("/tmp/dbos-bench/results_raw_pg_final.json")   as f: raw_pg_data   = json.load(f)
with open("/tmp/dbos-bench/results_raw_crdb_final.json") as f: raw_crdb_data = json.load(f)
with open("/tmp/dbos-bench/results_crdb_final.json")     as f: wf_crdb_data  = json.load(f)
with open("/tmp/dbos-bench/results_pg_final.json")       as f: wf_pg_data    = json.load(f)

raw_pg   = sorted(raw_pg_data["raw_writes"],   key=lambda x: x["concurrency"])
raw_crdb = sorted(raw_crdb_data["raw_writes"], key=lambda x: x["concurrency"])
wf_pg    = sorted(wf_pg_data["workflows"],     key=lambda x: x["concurrency"])
wf_crdb  = sorted(wf_crdb_data["workflows"],   key=lambda x: x["concurrency"])

conc           = [r["concurrency"] for r in raw_pg]
raw_pg_tput    = [r["throughput"]  for r in raw_pg]
raw_crdb_tput  = [r["throughput"]  for r in raw_crdb]
raw_pg_p50     = [r["p50"]         for r in raw_pg]
raw_crdb_p50   = [r["p50"]         for r in raw_crdb]

CRDB  = "#0055FF"
PG    = "#FF6B35"
GRID  = "#E8E8E8"
BG    = "#FAFAFA"

plt.rcParams.update({
    "font.family": "sans-serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
})

RAW_PG_PEAK   = max(raw_pg_tput)
RAW_CRDB_PEAK = max(raw_crdb_tput)
WF_PG_PEAK    = max(r["throughput"] for r in wf_pg)
WF_CRDB_PEAK  = max(r["throughput"] for r in wf_crdb)

# ── Chart 1: Raw write throughput — PG vs CRDB ───────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
ax.set_facecolor(BG)

ax.plot(conc, raw_pg_tput,   "s-", color=PG,   linewidth=2.5, markersize=7,
        label=f"PostgreSQL RDS 17 — raw INSERT (peak {RAW_PG_PEAK:,.0f} writes/s)")
ax.plot(conc, raw_crdb_tput, "o-", color=CRDB, linewidth=2.5, markersize=7,
        label=f"CockroachDB 3-node — raw INSERT (peak {RAW_CRDB_PEAK:,.0f} writes/s)")

ax.set_xlabel("Concurrent writers", fontsize=12)
ax.set_ylabel("Raw writes / second", fontsize=12)
ax.set_title(
    "Raw INSERT Throughput: PostgreSQL vs CockroachDB\n"
    "3-column table, single row per INSERT, autocommit — no application logic",
    fontsize=12, pad=14)
ax.set_xticks(conc)
ax.tick_params(axis='x', rotation=45)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.legend(fontsize=10)
fig.tight_layout()
for dest in ["/tmp/dbos-bench/dbos-bench-raw-throughput.png",
             f"{ASSET_DIR}/dbos-bench-raw-throughput.png"]:
    fig.savefig(dest, dpi=150, bbox_inches="tight")
plt.close()

# ── Chart 2: Four-bar summary — raw vs workflow at saturation ────────────────
labels  = ["Raw writes\nPostgreSQL", "Raw writes\nCockroachDB",
           "DBOS workflows\nPostgreSQL", "DBOS workflows\nCockroachDB"]
values  = [RAW_PG_PEAK, RAW_CRDB_PEAK, WF_PG_PEAK, WF_CRDB_PEAK]
colors  = [PG, CRDB, PG, CRDB]
hatches = ["", "", "///", "///"]

fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
ax.set_facecolor(BG)

bars = ax.bar(labels, values, color=colors, width=0.5, edgecolor="white", linewidth=1.2)
for bar, hatch, val in zip(bars, hatches, values):
    bar.set_hatch(hatch)
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.01,
            f"{val:,.0f}", ha="center", va="bottom", fontsize=11, fontweight="bold")

ax.set_ylabel("Throughput (ops/second)", fontsize=12)
ax.set_title(
    "Raw Writes vs DBOS Workflow Completions — Peak Throughput\n"
    "Solid = raw INSERT; hatched = real DBOS 2-step workflow end-to-end",
    fontsize=12, pad=14)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.set_ylim(0, max(values) * 1.15)

from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=PG,   label="PostgreSQL RDS 17"),
    Patch(facecolor=CRDB, label="CockroachDB 3-node"),
    Patch(facecolor="gray", hatch="///", label="DBOS 2-step workflow"),
]
ax.legend(handles=legend_elements, fontsize=10)
fig.tight_layout()
for dest in ["/tmp/dbos-bench/dbos-bench-raw-vs-workflow.png",
             f"{ASSET_DIR}/dbos-bench-raw-vs-workflow.png"]:
    fig.savefig(dest, dpi=150, bbox_inches="tight")
plt.close()

print("Charts saved.")
print(f"\nRaw write peak  — PG: {RAW_PG_PEAK:,.0f} writes/s   CRDB: {RAW_CRDB_PEAK:,.0f} writes/s")
print(f"Workflow peak   — PG: {WF_PG_PEAK:,.0f} wf/s         CRDB: {WF_CRDB_PEAK:,.0f} wf/s")
print(f"\nRaw→workflow ratio  — PG: {RAW_PG_PEAK/WF_PG_PEAK:.0f}×   CRDB: {RAW_CRDB_PEAK/WF_CRDB_PEAK:.0f}×")
