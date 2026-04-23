"""
Benchmark with direct node connections (no NLB), round-robin across 3 nodes.
"""
import time, statistics, os, json, psycopg2, itertools
from concurrent.futures import ThreadPoolExecutor, as_completed

NODE_IPS = ["13.222.72.12", "98.89.79.106", "100.24.96.151"]
DB_URLS  = [f"postgresql://root@{ip}:26257/dbos_system?sslmode=disable" for ip in NODE_IPS]
node_cycle = itertools.cycle(DB_URLS)

CONCURRENCY_LEVELS = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
WRITES_PER_LEVEL   = 200

def single_write(db_url):
    t0 = time.perf_counter()
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    with conn.cursor() as cur:
        cur.execute("INSERT INTO dbos_bench_writes (payload) VALUES (%s)", ("bench",))
    conn.commit()
    conn.close()
    return time.perf_counter() - t0

def bench_writes(concurrency, total):
    latencies = []
    urls = [next(node_cycle) for _ in range(total)]
    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [ex.submit(single_write, url) for url in urls]
        for f in as_completed(futures):
            try:
                latencies.append(f.result())
            except Exception as e:
                print(f"  error: {e}")
    elapsed = time.perf_counter() - t_start
    return latencies, elapsed

def percentile(data, p):
    data = sorted(data)
    idx = int(len(data) * p / 100)
    return data[min(idx, len(data)-1)]

write_results = []
print(f"\nDirect-node benchmark (round-robin across {NODE_IPS})")
print(f"{'Concurrency':>12} | {'Writes/s':>10} | {'p50 (ms)':>10} | {'p95 (ms)':>10} | {'p99 (ms)':>10}")
print("-" * 65)

for c in CONCURRENCY_LEVELS:
    lats, elapsed = bench_writes(c, WRITES_PER_LEVEL)
    tput = len(lats) / elapsed
    r = {
        "concurrency": c,
        "throughput": tput,
        "p50": percentile(lats, 50) * 1000,
        "p95": percentile(lats, 95) * 1000,
        "p99": percentile(lats, 99) * 1000,
        "mean": statistics.mean(lats) * 1000,
    }
    write_results.append(r)
    print(f"{c:>12} | {tput:>10.1f} | {r['p50']:>10.0f} | {r['p95']:>10.0f} | {r['p99']:>10.0f}", flush=True)

with open("/tmp/dbos-bench/results_direct.json", "w") as f:
    json.dump({"writes": write_results}, f, indent=2)
print("\nSaved to /tmp/dbos-bench/results_direct.json")
