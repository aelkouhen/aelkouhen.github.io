"""
DBOS workflow benchmark — full concurrency range c=1..512 via NLB.
Measures real durable workflow start+completion throughput on CockroachDB.
"""
import time, statistics, json, uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import create_engine
from dbos import DBOS, DBOSConfig, SetWorkflowID

NLB_URL  = "postgresql://root@nlb-20260423194342360500000006-a4145919c7a3e780.elb.us-east-1.amazonaws.com:26257/dbos_system?sslmode=disable"
CRDB_URL = NLB_URL.replace("postgresql://", "cockroachdb://", 1)

engine = create_engine(CRDB_URL, pool_size=64, max_overflow=128)

config: DBOSConfig = {
    "name":                   "bench-workflow",
    "system_database_url":    NLB_URL,
    "system_database_engine": engine,
    "use_listen_notify":      False,
}
DBOS(config=config)

# ── Workflow ──────────────────────────────────────────────────────────────

@DBOS.step()
def step_one(task_id: str) -> str:
    return f"done_{task_id}"

@DBOS.step()
def step_two(result: str) -> str:
    return f"committed_{result}"

@DBOS.workflow()
def bench_workflow(task_id: str) -> str:
    r1 = step_one(task_id)
    r2 = step_two(r1)
    return r2

# ── Helpers ───────────────────────────────────────────────────────────────

CONCURRENCY_LEVELS  = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
WORKFLOWS_PER_LEVEL = 200

def start_one() -> float:
    t0    = time.perf_counter()
    wf_id = str(uuid.uuid4())
    with SetWorkflowID(wf_id):
        handle = DBOS.start_workflow(bench_workflow, wf_id)
    handle.get_result()
    return time.perf_counter() - t0

def run_level(concurrency: int, total: int):
    latencies = []
    t_start   = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [ex.submit(start_one) for _ in range(total)]
        for f in as_completed(futures):
            try:
                latencies.append(f.result())
            except Exception as e:
                print(f"  error: {e}")
    elapsed = time.perf_counter() - t_start
    return latencies, elapsed

def percentile(data, p):
    data = sorted(data)
    idx  = int(len(data) * p / 100)
    return data[min(idx, len(data) - 1)]

# ── Run ───────────────────────────────────────────────────────────────────

DBOS.launch()

results = []
print(f"\nDBOS workflow benchmark via NLB — 3-node CockroachDB (96 vCPU)")
print(f"Workflow: 2 steps, wait for completion (end-to-end latency)")
print(f"{'Concurrency':>12} | {'Workflows/s':>12} | {'p50 (ms)':>10} | {'p95 (ms)':>10} | {'p99 (ms)':>10}")
print("-" * 70)

for c in CONCURRENCY_LEVELS:
    lats, elapsed = run_level(c, WORKFLOWS_PER_LEVEL)
    if not lats:
        print(f"{c:>12} | {'NO DATA':>12}")
        continue
    tput = len(lats) / elapsed
    r = {
        "concurrency": c,
        "throughput":  tput,
        "p50":         percentile(lats, 50) * 1000,
        "p95":         percentile(lats, 95) * 1000,
        "p99":         percentile(lats, 99) * 1000,
        "mean":        statistics.mean(lats) * 1000,
    }
    results.append(r)
    print(f"{c:>12} | {tput:>12.1f} | {r['p50']:>10.0f} | {r['p95']:>10.0f} | {r['p99']:>10.0f}", flush=True)

with open("/tmp/dbos-bench/results.json", "w") as f:
    json.dump({"workflows": results}, f, indent=2)
print("\nSaved to /tmp/dbos-bench/results.json")
