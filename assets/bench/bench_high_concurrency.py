"""
Benchmark only the high-concurrency levels (c=64..512) then merge with existing results.
"""
import time, statistics, os, json, psycopg2
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_URL = os.environ["DBOS_COCKROACHDB_URL"]
CONCURRENCY_LEVELS = [64, 128, 256, 512]
WRITES_PER_LEVEL = 200

def single_write(db_url):
    t0 = time.perf_counter()
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    with conn.cursor() as cur:
        cur.execute("INSERT INTO dbos_bench_writes (payload) VALUES (%s)", ("bench",))
    conn.commit()
    conn.close()
    return time.perf_counter() - t0

def bench_writes(db_url, concurrency, total):
    latencies = []
    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [ex.submit(single_write, db_url) for _ in range(total)]
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

# Load existing results
with open("/tmp/dbos-bench/results.json") as f:
    results = json.load(f)

print(f"\nExtending benchmark with high-concurrency levels: {CONCURRENCY_LEVELS}")
print(f"{'Concurrency':>12} | {'Writes/s':>10} | {'p50 (ms)':>10} | {'p95 (ms)':>10} | {'p99 (ms)':>10}")
print("-" * 65)

for c in CONCURRENCY_LEVELS:
    lats, elapsed = bench_writes(DB_URL, c, WRITES_PER_LEVEL)
    tput = len(lats) / elapsed
    r = {
        "concurrency": c,
        "throughput": tput,
        "p50": percentile(lats, 50) * 1000,
        "p95": percentile(lats, 95) * 1000,
        "p99": percentile(lats, 99) * 1000,
        "mean": statistics.mean(lats) * 1000,
    }
    results["writes"].append(r)
    print(f"{c:>12} | {tput:>10.1f} | {r['p50']:>10.0f} | {r['p95']:>10.0f} | {r['p99']:>10.0f}")

# Sort by concurrency
results["writes"].sort(key=lambda x: x["concurrency"])

with open("/tmp/dbos-bench/results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nResults saved to /tmp/dbos-bench/results.json")
