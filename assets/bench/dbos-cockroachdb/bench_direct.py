"""
DBOS workflow benchmark — full concurrency range c=1..512, round-robin across 3 direct node IPs.
Connection pool uses a custom creator that cycles connections across nodes, bypassing the NLB.
"""
import time, statistics, json, uuid, itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import create_engine, event
from sqlalchemy.pool import QueuePool
import psycopg2
from dbos import DBOS, DBOSConfig, SetWorkflowID

# Patch: SQLAlchemy PostgreSQL dialect version regex doesn't handle CockroachDB v26.x
from sqlalchemy.dialects.postgresql import base as _pg_base
import sqlalchemy_cockroachdb.base as _crdb_base

def _patched_ver(self, conn):
    try:
        v = conn.exec_driver_sql("SELECT version()").scalar()
        import re
        m = re.search(r"v(\d+)\.(\d+)\.(\d+)", v)
        if m:
            return tuple(int(x) for x in m.groups())
        return (26, 1, 3)
    except Exception:
        return (26, 1, 3)

_pg_base.PGDialect._get_server_version_info = _patched_ver
_crdb_base.CockroachDBDialect._get_server_version_info = _patched_ver

NODE_IPS = ["18.209.130.220", "100.51.81.217", "44.207.208.13"]
NLB_URL  = "postgresql://root@nlb-20260423194342360500000006-a4145919c7a3e780.elb.us-east-1.amazonaws.com:26257/dbos_system?sslmode=disable"

# Round-robin creator: each new connection goes to the next node in sequence
_ip_cycle = itertools.cycle(NODE_IPS)

def _creator():
    ip  = next(_ip_cycle)
    url = f"postgresql://root@{ip}:26257/dbos_system?sslmode=disable"
    return psycopg2.connect(url)

engine = create_engine(
    "cockroachdb+psycopg2://",
    creator=_creator,
    poolclass=QueuePool,
    pool_size=64,
    max_overflow=128,
)

config: DBOSConfig = {
    "name":                   "bench-workflow-direct",
    "system_database_url":    NLB_URL,   # DBOS migrations use NLB; data ops use the pool above
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

CONCURRENCY_LEVELS = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
DURATION_PER_LEVEL = 30   # seconds per level — submit continuously, drain at deadline

def start_one() -> float:
    t0    = time.perf_counter()
    wf_id = str(uuid.uuid4())
    with SetWorkflowID(wf_id):
        handle = DBOS.start_workflow(bench_workflow, wf_id)
    handle.get_result()
    return time.perf_counter() - t0

def run_level(concurrency: int, duration: float):
    latencies   = []
    deadline    = time.perf_counter() + duration
    in_flight   = []
    t_start     = time.perf_counter()

    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        # Fill up to concurrency workers, keep refilling until deadline
        while True:
            # Harvest completed futures
            still_running = []
            for f in in_flight:
                if f.done():
                    try:
                        latencies.append(f.result())
                    except Exception as e:
                        print(f"  error: {e}")
                else:
                    still_running.append(f)
            in_flight = still_running

            if time.perf_counter() >= deadline:
                break

            # Top up the pool
            while len(in_flight) < concurrency:
                in_flight.append(ex.submit(start_one))

            time.sleep(0.005)

        # Drain remaining in-flight workflows
        for f in as_completed(in_flight):
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
print(f"\nDBOS workflow benchmark — direct node IPs {NODE_IPS}")
print(f"Workflow: 2 steps, wait for completion (end-to-end latency)")
print(f"{'Concurrency':>12} | {'Workflows/s':>12} | {'p50 (ms)':>10} | {'p95 (ms)':>10} | {'p99 (ms)':>10}")
print("-" * 70)

for c in CONCURRENCY_LEVELS:
    lats, elapsed = run_level(c, DURATION_PER_LEVEL)
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

with open("/tmp/dbos-bench/results_direct.json", "w") as f:
    json.dump({"workflows": results}, f, indent=2)
print("\nSaved to /tmp/dbos-bench/results_direct.json")
