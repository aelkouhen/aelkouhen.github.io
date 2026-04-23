"""
DBOS workflow benchmark — PostgreSQL RDS 17, READ COMMITTED isolation (explicit).
db.m7i.24xlarge 96 vCPU, gp3 500 GiB, 16K IOPS, us-east-1.
"""
import time, statistics, json, uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from dbos import DBOS, DBOSConfig, SetWorkflowID

PG_URL = "postgresql://postgres:password@benchmark.chp2kwqyznpo.us-east-1.rds.amazonaws.com:5432/postgres"

engine = create_engine(
    PG_URL,
    poolclass=QueuePool,
    pool_size=128,
    max_overflow=256,
    isolation_level="READ COMMITTED",   # PG default, but explicit for parity
)

config: DBOSConfig = {
    "name":                   "bench-workflow-pg-rc",
    "system_database_url":    PG_URL,
    "system_database_engine": engine,
    "use_listen_notify":      False,
}
DBOS(config=config)

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

CONCURRENCY_LEVELS = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
DURATION_PER_LEVEL = 30

def start_one() -> float:
    t0    = time.perf_counter()
    wf_id = str(uuid.uuid4())
    with SetWorkflowID(wf_id):
        handle = DBOS.start_workflow(bench_workflow, wf_id)
    handle.get_result()
    return time.perf_counter() - t0

def run_level(concurrency: int, duration: float):
    latencies = []
    deadline  = time.perf_counter() + duration
    in_flight = []
    t_start   = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        while True:
            still_running = []
            for f in in_flight:
                if f.done():
                    try:    latencies.append(f.result())
                    except Exception as e: print(f"  error: {e}")
                else:
                    still_running.append(f)
            in_flight = still_running
            if time.perf_counter() >= deadline:
                break
            while len(in_flight) < concurrency:
                in_flight.append(ex.submit(start_one))
            time.sleep(0.005)
        for f in as_completed(in_flight):
            try:    latencies.append(f.result())
            except Exception as e: print(f"  error: {e}")
    elapsed = time.perf_counter() - t_start
    return latencies, elapsed

def percentile(data, p):
    data = sorted(data)
    idx  = int(len(data) * p / 100)
    return data[min(idx, len(data) - 1)]

DBOS.launch()

results = []
print(f"\nDBOS workflow benchmark — PostgreSQL RDS 17 READ COMMITTED, co-located us-east-1")
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

with open("/home/ubuntu/results_pg_rc.json", "w") as f:
    json.dump({"workflows": results}, f, indent=2)
print("\nSaved to /home/ubuntu/results_pg_rc.json")
