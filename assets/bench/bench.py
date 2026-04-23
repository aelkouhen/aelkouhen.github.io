"""
DBOS workflow start throughput benchmark against CockroachDB.
Measures raw write throughput and workflow start latency at varying concurrency levels.
"""
import asyncio
import time
import statistics
import os
import json
import psycopg2
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_URL = os.environ["DBOS_COCKROACHDB_URL"]

CONCURRENCY_LEVELS = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
WRITES_PER_LEVEL = 200  # total writes per concurrency level


# ── Raw write benchmark ────────────────────────────────────────────────────

def setup_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dbos_bench_writes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                payload TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT now()
            )
        """)
        conn.commit()

def single_write(db_url):
    t0 = time.perf_counter()
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    with conn.cursor() as cur:
        cur.execute("INSERT INTO dbos_bench_writes (payload) VALUES (%s)", ("bench",))
    conn.commit()
    conn.close()
    return time.perf_counter() - t0

def bench_writes_at_concurrency(db_url, concurrency, total):
    latencies = []
    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [ex.submit(single_write, db_url) for _ in range(total)]
        for f in as_completed(futures):
            try:
                latencies.append(f.result())
            except Exception:
                pass
    elapsed = time.perf_counter() - t_start
    return latencies, elapsed


# ── DBOS workflow benchmark (via HTTP) ─────────────────────────────────────

import urllib.request
import urllib.parse

BASE_URL = "http://localhost:8000"

def start_workflow(task_id):
    t0 = time.perf_counter()
    url = f"{BASE_URL}/agent/{task_id}?task=bench"
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()
    return time.perf_counter() - t0

def bench_workflows_at_concurrency(concurrency, total, offset=0):
    latencies = []
    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = {
            ex.submit(start_workflow, f"bench-{offset+i}"): i
            for i in range(total)
        }
        for f in as_completed(futures):
            try:
                latencies.append(f.result())
            except Exception:
                pass
    elapsed = time.perf_counter() - t_start
    return latencies, elapsed


def percentile(data, p):
    data = sorted(data)
    idx = int(len(data) * p / 100)
    return data[min(idx, len(data) - 1)]


def run_benchmark():
    conn = psycopg2.connect(DB_URL)
    setup_table(conn)
    conn.close()

    write_results = []
    workflow_results = []
    wf_offset = 0

    print(f"\n{'Concurrency':>12} | {'Writes/s':>10} | {'p50 (ms)':>10} | {'p95 (ms)':>10} | {'p99 (ms)':>10}")
    print("-" * 62)

    for c in CONCURRENCY_LEVELS:
        # Raw writes
        lats, elapsed = bench_writes_at_concurrency(DB_URL, c, WRITES_PER_LEVEL)
        tput = len(lats) / elapsed
        write_results.append({
            "concurrency": c,
            "throughput": tput,
            "p50": percentile(lats, 50) * 1000,
            "p95": percentile(lats, 95) * 1000,
            "p99": percentile(lats, 99) * 1000,
            "mean": statistics.mean(lats) * 1000,
        })
        print(f"{'Raw writes':>12} c={c}: {tput:>8.1f}/s  p50={percentile(lats,50)*1000:.0f}ms  p95={percentile(lats,95)*1000:.0f}ms  p99={percentile(lats,99)*1000:.0f}ms")

        # Workflow starts
        lats_wf, elapsed_wf = bench_workflows_at_concurrency(c, WRITES_PER_LEVEL, wf_offset)
        wf_offset += WRITES_PER_LEVEL
        tput_wf = len(lats_wf) / elapsed_wf
        workflow_results.append({
            "concurrency": c,
            "throughput": tput_wf,
            "p50": percentile(lats_wf, 50) * 1000,
            "p95": percentile(lats_wf, 95) * 1000,
            "p99": percentile(lats_wf, 99) * 1000,
            "mean": statistics.mean(lats_wf) * 1000,
        })
        print(f"{'WF starts':>12} c={c}: {tput_wf:>8.1f}/s  p50={percentile(lats_wf,50)*1000:.0f}ms  p95={percentile(lats_wf,95)*1000:.0f}ms  p99={percentile(lats_wf,99)*1000:.0f}ms")
        print()

    results = {"writes": write_results, "workflows": workflow_results}
    with open("/tmp/dbos-bench/results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to /tmp/dbos-bench/results.json")
    return results


if __name__ == "__main__":
    run_benchmark()
