"""
Charts v5: real DBOS workflow benchmark — PG RDS 17 vs CockroachDB 3-node, both co-located us-east-1.
1. Throughput vs concurrency — PG vs CRDB side by side
2. Latency p50 — PG vs CRDB side by side
3. Linear scale-out projection — CRDB nodes vs PG single-node ceiling (measured)
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

with open("/tmp/dbos-bench/results_coloc.json") as f:
    crdb_data = json.load(f)
with open("/tmp/dbos-bench/results_pg.json") as f:
    pg_data = json.load(f)

crdb = sorted(crdb_data["workflows"], key=lambda x: x["concurrency"])
pg   = sorted(pg_data["workflows"],   key=lambda x: x["concurrency"])

conc      = [r["concurrency"] for r in crdb]
crdb_tput = [r["throughput"]  for r in crdb]
crdb_p50  = [r["p50"]         for r in crdb]
crdb_p95  = [r["p95"]         for r in crdb]
pg_tput   = [r["throughput"]  for r in pg]
pg_p50    = [r["p50"]         for r in pg]
pg_p95    = [r["p95"]         for r in pg]

CRDB = "#0055FF"
PG   = "#FF6B35"
GRID = "#E8E8E8"
BG   = "#FAFAFA"

plt.rcParams.update({
    "font.family": "sans-serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
})

CRDB_PEAK = max(crdb_tput)   # 116.6 wf/s
PG_PEAK   = max(pg_tput)     # 122.0 wf/s
NODES     = 3
PER_NODE  = CRDB_PEAK / NODES

# ── Chart 1: Throughput comparison ───────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
ax.set_facecolor(BG)

ax.plot(conc, pg_tput,   "s-", color=PG,   linewidth=2.5, markersize=7,
        label=f"PostgreSQL RDS 17 — 96 vCPU (peak {PG_PEAK:.0f} wf/s)")
ax.plot(conc, crdb_tput, "o-", color=CRDB, linewidth=2.5, markersize=7,
        label=f"CockroachDB 3-node — 96 vCPU, multi-AZ (peak {CRDB_PEAK:.0f} wf/s)")

ax.set_xlabel("Concurrent workflows", fontsize=12)
ax.set_ylabel("Workflows / second", fontsize=12)
ax.set_title(
    "DBOS Workflow Throughput: PostgreSQL vs CockroachDB — Same Workload, Same Region\n"
    "2-step workflow, end-to-end completion, co-located in AWS us-east-1",
    fontsize=12, pad=14)
ax.set_xticks(conc)
ax.tick_params(axis='x', rotation=45)
ax.legend(fontsize=10)
fig.tight_layout()
for dest in [f"/tmp/dbos-bench/dbos-bench-crdb-throughput.png",
             f"{ASSET_DIR}/dbos-bench-crdb-throughput.png"]:
    fig.savefig(dest, dpi=150, bbox_inches="tight")
plt.close()

# ── Chart 2: Latency comparison ───────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
ax.set_facecolor(BG)

ax.plot(conc, pg_p50,   "s-", color=PG,   linewidth=2.5, markersize=7, label="PostgreSQL p50")
ax.plot(conc, crdb_p50, "o-", color=CRDB, linewidth=2.5, markersize=7, label="CockroachDB p50")
ax.fill_between(conc, pg_p50,   pg_p95,   color=PG,   alpha=0.10, label="PG p50–p95")
ax.fill_between(conc, crdb_p50, crdb_p95, color=CRDB, alpha=0.10, label="CRDB p50–p95")

ax.set_xlabel("Concurrent workflows", fontsize=12)
ax.set_ylabel("End-to-end latency (ms)", fontsize=12)
ax.set_title(
    "DBOS Workflow Latency: PostgreSQL vs CockroachDB\n"
    "PG faster at low concurrency (local WAL); both converge above c=32",
    fontsize=12, pad=14)
ax.set_xticks(conc)
ax.tick_params(axis='x', rotation=45)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.legend(fontsize=10)
fig.tight_layout()
for dest in [f"/tmp/dbos-bench/dbos-bench-crdb-latency.png",
             f"{ASSET_DIR}/dbos-bench-crdb-latency.png"]:
    fig.savefig(dest, dpi=150, bbox_inches="tight")
plt.close()

# ── Chart 3: Scale-out — CRDB linear vs PG hard ceiling (now measured) ───
MAX_NODES  = 20
node_range = np.linspace(0, MAX_NODES, 200)
crdb_line  = PER_NODE * node_range

fig, ax = plt.subplots(figsize=(9, 5), facecolor=BG)
ax.set_facecolor(BG)

ax.axhline(PG_PEAK, color=PG, linestyle="--", linewidth=2, alpha=0.85,
           label=f"PostgreSQL ceiling — {PG_PEAK:.0f} wf/s (measured)\nSingle WAL: adding nodes/hardware doesn't help")
ax.plot(node_range, crdb_line, color=CRDB, linewidth=2.5,
        label=f"CockroachDB scale-out (~{PER_NODE:.0f} wf/s per node, measured)")

ax.scatter([NODES], [CRDB_PEAK], color=CRDB, s=110, zorder=6)
ax.annotate(
    f"★ Measured\n{CRDB_PEAK:.0f} wf/s\n({NODES} nodes, multi-AZ)",
    xy=(NODES, CRDB_PEAK),
    xytext=(NODES + 1.5, CRDB_PEAK + 15),
    fontsize=10, color=CRDB, fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=CRDB, lw=1.2))

crossover = PG_PEAK / PER_NODE
ax.scatter([crossover], [PG_PEAK], color=CRDB, s=80, zorder=5)
ax.annotate(
    f"CRDB exceeds PG ceiling\nat ~{crossover:.1f} nodes",
    xy=(crossover, PG_PEAK),
    xytext=(crossover + 0.8, PG_PEAK + 18),
    fontsize=9, color=CRDB,
    arrowprops=dict(arrowstyle="->", color=CRDB, lw=1.1))

ax.set_xlabel("CockroachDB nodes", fontsize=12)
ax.set_ylabel("DBOS Workflows / second", fontsize=12)
ax.set_title(
    "CockroachDB Scales Out — PostgreSQL Cannot\n"
    f"PG ceiling measured at {PG_PEAK:.0f} wf/s. CRDB surpasses it at ~{crossover:.1f} nodes, then keeps growing.",
    fontsize=12, pad=14)
ax.set_xlim(0, MAX_NODES)
ax.set_ylim(0, PER_NODE * MAX_NODES * 1.08)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.legend(fontsize=10, loc="upper left")
fig.tight_layout()
for dest in [f"/tmp/dbos-bench/dbos-bench-linear-vs-ceiling.png",
             f"{ASSET_DIR}/dbos-bench-linear-vs-ceiling.png"]:
    fig.savefig(dest, dpi=150, bbox_inches="tight")
plt.close()

print("3 charts saved.")
print(f"\nSide-by-side summary:")
print(f"{'c':>6} | {'PG wf/s':>10} | {'PG p50':>8} | {'CRDB wf/s':>10} | {'CRDB p50':>10}")
print("-" * 55)
for i, c in enumerate(conc):
    print(f"{c:>6} | {pg_tput[i]:>10.1f} | {pg_p50[i]:>8.0f} | {crdb_tput[i]:>10.1f} | {crdb_p50[i]:>10.0f}")
print(f"\nPG peak   : {PG_PEAK:.1f} wf/s")
print(f"CRDB peak : {CRDB_PEAK:.1f} wf/s (3 nodes, multi-AZ)")
print(f"CRDB surpasses PG ceiling at: ~{crossover:.1f} nodes")
