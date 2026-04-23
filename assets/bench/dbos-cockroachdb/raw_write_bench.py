#!/usr/bin/env python3
"""
raw_write_bench.py — simple 3-column INSERT benchmark.

Mirrors the DBOS blog raw-write methodology: concurrent INSERT threads,
time-bounded per concurrency level, no application logic between writes.
Each INSERT touches a single row in a 3-column table (id, val, ts) —
the smallest possible write unit, identical to the DBOS blog's baseline.

Usage:
  python3 raw_write_bench.py --db pg
  python3 raw_write_bench.py --db crdb
"""
import argparse, itertools, json, statistics, threading, time
import psycopg2

PG_DSN   = "postgresql://postgres:password@benchmark.chp2kwqyznpo.us-east-1.rds.amazonaws.com:5432/postgres"
NODE_IPS = ["100.55.236.85", "54.204.219.108", "3.226.145.29"]
_ip_cycle = itertools.cycle(NODE_IPS)

LEVELS   = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
DURATION = 30   # seconds per level

DDL_PG = """
CREATE TABLE IF NOT EXISTS raw_bench (
    id  BIGSERIAL    PRIMARY KEY,
    val TEXT         NOT NULL,
    ts  TIMESTAMPTZ  NOT NULL DEFAULT now()
)
"""
DDL_CRDB = """
CREATE TABLE IF NOT EXISTS raw_bench (
    id  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    val STRING       NOT NULL,
    ts  TIMESTAMPTZ  NOT NULL DEFAULT now()
)
"""
INSERT = "INSERT INTO raw_bench (val) VALUES (%s)"


def make_pg():
    return psycopg2.connect(PG_DSN)

def make_crdb():
    ip = next(_ip_cycle)
    return psycopg2.connect(
        f"postgresql://root@{ip}:26257/defaultdb?sslmode=disable"
    )


def worker(make_conn, stop_evt, latencies, errors):
    try:
        conn = make_conn()
        conn.autocommit = True
        cur  = conn.cursor()
        while not stop_evt.is_set():
            t0 = time.perf_counter()
            try:
                cur.execute(INSERT, ("x",))
                latencies.append((time.perf_counter() - t0) * 1000)
            except Exception as e:
                errors.append(1)
        cur.close()
        conn.close()
    except Exception as e:
        errors.append(1)


def run_level(concurrency, make_conn):
    stop_evt  = threading.Event()
    latencies = []
    errors    = []
    threads   = [
        threading.Thread(
            target=worker,
            args=(make_conn, stop_evt, latencies, errors),
            daemon=True,
        )
        for _ in range(concurrency)
    ]
    for t in threads:
        t.start()
    time.sleep(DURATION)
    stop_evt.set()
    for t in threads:
        t.join(timeout=5)

    if len(latencies) < 2:
        return None
    s = sorted(latencies)
    n = len(s)
    return {
        "concurrency": concurrency,
        "writes":      n,
        "throughput":  round(n / DURATION, 2),
        "p50":         round(s[int(n * 0.50)], 3),
        "p95":         round(s[int(n * 0.95)], 3),
        "p99":         round(s[int(n * 0.99)], 3),
        "mean":        round(statistics.mean(s), 3),
        "errors":      len(errors),
    }


def setup(make_conn, ddl):
    conn = make_conn()
    conn.autocommit = True
    cur  = conn.cursor()
    cur.execute(ddl)
    cur.execute("DELETE FROM raw_bench")   # clear previous runs; keep schema
    cur.close()
    conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db",  choices=["pg", "crdb"], required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.db == "pg":
        make_conn = make_pg
        ddl       = DDL_PG
        out_file  = args.out or "/home/ubuntu/results_raw_pg.json"
    else:
        make_conn = make_crdb
        ddl       = DDL_CRDB
        out_file  = args.out or "/home/ubuntu/results_raw_crdb.json"

    print(f"[setup] creating table for {args.db} …")
    setup(make_conn, ddl)

    results = []
    print(f"{'c':>6} | {'writes/s':>10} | {'p50 ms':>8} | {'p95 ms':>8} | errors")
    print("-" * 55)
    for c in LEVELS:
        r = run_level(c, make_conn)
        if r:
            results.append(r)
            print(f"{c:>6} | {r['throughput']:>10.0f} | {r['p50']:>8.1f} | "
                  f"{r['p95']:>8.1f} | {r['errors']}")
        else:
            print(f"{c:>6} | {'(no data)':>10}")

    with open(out_file, "w") as f:
        json.dump({"raw_writes": results}, f, indent=2)
    print(f"\nSaved → {out_file}")


if __name__ == "__main__":
    main()
