#!/usr/bin/env python3
"""
bench_multiproc.py — DBOS workflow throughput on PostgreSQL and CockroachDB,
faithful port of the official DBOS harness methodology:
https://github.com/dbos-inc/dbos-postgres-benchmark (benchmarks/dbos_start_workflow.py)

Methodology (identical to the official benchmark):
  * N spawned worker processes, each with its own DBOS runtime + asyncio loop
  * Phase 1: fire-and-forget start_workflow_async in concurrent batches at a
    target aggregate rate (no per-handle get_result)
  * Phase 2: drain — worker 0 polls list_workflows(status=PENDING) until empty
  * Completion RPS = total started / (last drain end - first start)
  * Latency: sampled workflows only, computed from dbos.workflow_status.updated_at

Additions vs the original:
  * --db crdb: round-robin direct node IPs, Read Committed isolation,
    listen/notify disabled, sqlalchemy-cockroachdb version-regex patch
  * --steps N: N-step workflow. N=0 reproduces the official no-op (2 system
    writes); N=2 reproduces the datacrafterslab article workflow (4 writes)

Usage:
  python3 bench_multiproc.py --db pg \
      --url "postgresql://postgres:password@host:5432/dbos_bench" \
      --rps 2000 --processes 32 --steps 2

  python3 bench_multiproc.py --db crdb \
      --nodes 10.0.0.1,10.0.0.2,10.0.0.3 \
      --rps 2000 --processes 32 --steps 2

Size --processes to the client machine: the official run used 256 processes on
a c7i.48xlarge (192 vCPU). A single process saturates around ~120 wf/s, so
aggregate throughput is roughly capped by processes x 120 until the database
becomes the real bottleneck.
"""

import argparse
import asyncio
import itertools
import json
import multiprocessing as mp
import os
import random
import time
import uuid

import psycopg2


def percentile(values, pct):
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round(pct / 100 * (len(s) - 1)))))
    return s[k]


# ── Database-specific plumbing ────────────────────────────────────────────


def crdb_dsn(ip, database):
    return f"postgresql://root@{ip}:26257/{database}?sslmode=disable"


def patch_crdb_dialect():
    """sqlalchemy / sqlalchemy-cockroachdb cannot parse CRDB v26 version strings."""
    import re

    from sqlalchemy.dialects.postgresql import base as _pg_base
    import sqlalchemy_cockroachdb.base as _crdb_base

    def _patched_ver(self, conn):
        try:
            v = conn.exec_driver_sql("SELECT version()").scalar()
            m = re.search(r"v(\d+)\.(\d+)\.(\d+)", v)
            if m:
                return tuple(int(x) for x in m.groups())
            return (26, 1, 3)
        except Exception:
            return (26, 1, 3)

    _pg_base.PGDialect._get_server_version_info = _patched_ver
    _crdb_base.CockroachDBDialect._get_server_version_info = _patched_ver


def make_crdb_engine(nodes, database, pool_size):
    from sqlalchemy import create_engine
    from sqlalchemy.pool import QueuePool

    patch_crdb_dialect()
    ip_cycle = itertools.cycle(nodes)

    def _creator():
        conn = psycopg2.connect(crdb_dsn(next(ip_cycle), database))
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SET default_transaction_isolation = 'read committed'")
        conn.autocommit = False
        return conn

    return create_engine(
        "cockroachdb+psycopg2://",
        creator=_creator,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=pool_size * 2,
        isolation_level="READ COMMITTED",
    )


def make_dbos_config(cfg, pool_size, executor_threads):
    """Build a DBOSConfig dict; must be called inside the target process."""
    config = {
        "name": "dbos-bench",
        "run_admin_server": False,
        "max_executor_threads": executor_threads,
        "executor_id": str(uuid.uuid4()),
    }
    if cfg["db"] == "crdb":
        config["system_database_url"] = cfg["dsn"]
        config["system_database_engine"] = make_crdb_engine(
            cfg["nodes"], cfg["database"], pool_size
        )
        config["use_listen_notify"] = False
    else:
        config["system_database_url"] = cfg["dsn"]
        config["sys_db_pool_size"] = pool_size
    return config


def recreate_database(cfg):
    """Drop and recreate the benchmark database."""
    if cfg["db"] == "pg":
        conn = psycopg2.connect(cfg["admin_url"])
        drop = f'DROP DATABASE IF EXISTS "{cfg["database"]}" WITH (FORCE)'
    else:
        conn = psycopg2.connect(crdb_dsn(cfg["nodes"][0], "defaultdb"))
        drop = f'DROP DATABASE IF EXISTS "{cfg["database"]}" CASCADE'
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(drop)
            cur.execute(f'CREATE DATABASE "{cfg["database"]}"')
    finally:
        conn.close()


def bootstrap_schema_entry(cfg):
    """Pre-create the DBOS system schema in a one-shot subprocess so workers
    don't serialize on the migration advisory lock (same as official)."""
    from dbos import DBOS

    DBOS(config=make_dbos_config(cfg, pool_size=2, executor_threads=4))
    DBOS.launch()
    DBOS.destroy()


# ── Worker process (mirrors official worker_entry) ────────────────────────


def worker_entry(
    worker_id,
    cfg,
    target_rps,
    duration_s,
    start_batch_size,
    pool_size,
    executor_threads,
    sample_rate,
    start_done_barrier,
    done_barrier,
    result_queue,
):
    from dbos import DBOS

    n_steps = cfg["steps"]

    @DBOS.step()
    async def bench_step(i: int) -> int:
        return i

    @DBOS.workflow()
    async def bench_workflow(steps: int) -> int:
        for i in range(steps):
            await bench_step(i)
        return 1

    DBOS(config=make_dbos_config(cfg, pool_size, executor_threads))
    DBOS.launch()

    samples = []  # (workflow_id, start_wallclock_seconds)

    async def start_one():
        sampled = random.random() < sample_rate
        start = time.time() if sampled else 0.0
        handle = await DBOS.start_workflow_async(bench_workflow, n_steps)
        if sampled:
            samples.append((handle.workflow_id, start))

    async def start_batch():
        await asyncio.gather(*(start_one() for _ in range(start_batch_size)))
        return start_batch_size

    async def run():
        batches_per_second = target_rps / start_batch_size
        interval = 1.0 / batches_per_second
        total_batches = int(batches_per_second * duration_s)

        started = 0
        start_failures = 0

        # --- Phase 1: start workflows at target rate ---
        start_start_wall = time.time()
        loop_start = time.monotonic()
        for i in range(total_batches):
            target_time = loop_start + i * interval
            now = time.monotonic()
            if target_time > now:
                await asyncio.sleep(target_time - now)
            try:
                started += await start_batch()
            except Exception:
                start_failures += 1
        start_end_wall = time.time()
        print(
            f"[pid {os.getpid()}] start done: "
            f"{started} workflows in {start_end_wall - start_start_wall:.2f}s",
            flush=True,
        )

        await asyncio.to_thread(start_done_barrier.wait)

        # --- Phase 2: drain (worker 0 polls list_workflows) ---
        drain_start_wall = time.time()
        drain_end_wall = drain_start_wall
        if worker_id == 0:
            while True:
                unfinished = await DBOS.list_workflows_async(status="PENDING", limit=1)
                if not unfinished:
                    break
                await asyncio.sleep(0.1)
            drain_end_wall = time.time()
            print(
                f"[pid {os.getpid()}] drain done in {drain_end_wall - drain_start_wall:.2f}s",
                flush=True,
            )

        await asyncio.to_thread(done_barrier.wait)

        # --- Latency lookup from dbos.workflow_status.updated_at ---
        latencies = []
        if samples:
            conn = psycopg2.connect(cfg["dsn"])
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT workflow_uuid, updated_at FROM dbos.workflow_status "
                        "WHERE workflow_uuid = ANY(%s)",
                        ([s[0] for s in samples],),
                    )
                    rows = cur.fetchall()
            finally:
                conn.close()
            updated_at_by_id = {r[0]: r[1] for r in rows}
            for wf_id, start in samples:
                ua = updated_at_by_id.get(wf_id)
                if ua is None:
                    continue
                # updated_at is epoch milliseconds
                latencies.append(float(ua) / 1000.0 - start)

        return {
            "started": started,
            "start_failures": start_failures,
            "start_start_wall": start_start_wall,
            "start_end_wall": start_end_wall,
            "drain_start_wall": drain_start_wall,
            "drain_end_wall": drain_end_wall,
            "latencies": latencies,
        }

    try:
        result = asyncio.run(run())
        result_queue.put(result)
    finally:
        DBOS.destroy()


# ── Orchestration (mirrors official run_multiprocess) ─────────────────────


def run_multiprocess(cfg, total_rps, duration_s, start_batch_size, pool_size,
                     executor_threads, processes, sample_rate, out_path):
    recreate_database(cfg)

    per_proc_rps = max(1, total_rps // processes)

    ctx = mp.get_context("spawn")

    bootstrap = ctx.Process(target=bootstrap_schema_entry, args=(cfg,))
    bootstrap.start()
    bootstrap.join()
    if bootstrap.exitcode != 0:
        raise SystemExit("schema bootstrap failed")

    result_queue = ctx.Queue()
    start_done_barrier = ctx.Barrier(processes)
    done_barrier = ctx.Barrier(processes)
    workers = []
    for worker_id in range(processes):
        p = ctx.Process(
            target=worker_entry,
            args=(
                worker_id, cfg, per_proc_rps, duration_s, start_batch_size,
                pool_size, executor_threads, sample_rate,
                start_done_barrier, done_barrier, result_queue,
            ),
        )
        p.start()
        workers.append(p)

    results = [result_queue.get() for _ in workers]
    for p in workers:
        p.join()

    started = sum(r["started"] for r in results)
    start_failures = sum(r["start_failures"] for r in results)
    first_start = min(r["start_start_wall"] for r in results)
    last_start_end = max(r["start_end_wall"] for r in results)
    last_drain_end = max(r["drain_end_wall"] for r in results)
    start_time = last_start_end - first_start
    drain_time = last_drain_end - last_start_end
    total_time = last_drain_end - first_start
    start_rps = started / start_time if start_time > 0 else 0
    completion_rps = started / total_time if total_time > 0 else 0
    all_latencies = []
    for r in results:
        all_latencies.extend(r["latencies"])

    summary = {
        "db": cfg["db"],
        "steps": cfg["steps"],
        "processes": processes,
        "target_rps": total_rps,
        "start_batch": start_batch_size,
        "pool_size_per_proc": pool_size,
        "executor_threads_per_proc": executor_threads,
        "start_time_s": round(start_time, 2),
        "drain_time_s": round(drain_time, 2),
        "total_time_s": round(total_time, 2),
        "started": started,
        "start_failures": start_failures,
        "start_rps": round(start_rps),
        "completion_rps": round(completion_rps),
        "latency_samples": len(all_latencies),
        "p50_ms": round(percentile(all_latencies, 50) * 1000, 1),
        "p95_ms": round(percentile(all_latencies, 95) * 1000, 1),
        "p99_ms": round(percentile(all_latencies, 99) * 1000, 1),
    }

    print(f"\nDatabase:         {cfg['db']}  (steps={cfg['steps']})")
    print(f"Processes:        {processes}")
    print(f"Target RPS:       {total_rps}  ({per_proc_rps}/proc)")
    print(f"Start time:       {start_time:.2f}s")
    print(f"Drain time:       {drain_time:.2f}s")
    print(f"Total time:       {total_time:.2f}s")
    print(f"Started:          {started}")
    print(f"Start failures:   {start_failures}")
    print(f"Start RPS:        {start_rps:.0f}")
    print(f"Completion RPS:   {completion_rps:.0f}   (end-to-end)")
    if all_latencies:
        print(
            f"Latency samples:  {len(all_latencies)}   "
            f"p50={summary['p50_ms']}ms p95={summary['p95_ms']}ms "
            f"p99={summary['p99_ms']}ms"
        )

    if out_path:
        existing = []
        if os.path.exists(out_path):
            with open(out_path) as f:
                existing = json.load(f)
        existing.append(summary)
        with open(out_path, "w") as f:
            json.dump(existing, f, indent=2)
        print(f"\nAppended summary to {out_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", choices=["pg", "crdb"], required=True)
    parser.add_argument("--url", help="PG benchmark database URL (db=pg)")
    parser.add_argument(
        "--admin-url",
        help="PG admin URL for DROP/CREATE DATABASE (default: --url with /postgres)",
    )
    parser.add_argument("--nodes", help="Comma-separated CRDB node IPs (db=crdb)")
    parser.add_argument(
        "--database", default="dbos_bench", help="Benchmark database name (crdb)"
    )
    parser.add_argument("--rps", type=int, required=True,
                        help="Total target workflow starts per second")
    parser.add_argument("--duration", type=float, default=30.0,
                        help="Start phase duration in seconds")
    parser.add_argument("--start-batch", type=int, default=100,
                        help="Concurrent starts per batch (Phase 1)")
    parser.add_argument("--pool-size", type=int, default=2,
                        help="DBOS system DB pool size per process")
    parser.add_argument("--executor-threads", type=int, default=512,
                        help="DBOS max_executor_threads per process")
    parser.add_argument("--processes", type=int, default=32,
                        help="Worker processes (official run used 256 on 192 vCPU)")
    parser.add_argument("--sample-rate", type=float, default=0.01,
                        help="Fraction of workflows sampled for latency")
    parser.add_argument("--steps", type=int, default=0,
                        help="Steps per workflow: 0=official no-op, 2=article workflow")
    parser.add_argument("--out", help="JSON file to append the run summary to")
    args = parser.parse_args()

    cfg = {"db": args.db, "steps": args.steps, "database": args.database}
    if args.db == "pg":
        if not args.url:
            parser.error("--url is required with --db pg")
        cfg["dsn"] = args.url
        from urllib.parse import urlparse
        parsed = urlparse(args.url)
        cfg["database"] = parsed.path.lstrip("/")
        cfg["admin_url"] = args.admin_url or args.url.replace(
            "/" + cfg["database"], "/postgres"
        )
    else:
        if not args.nodes:
            parser.error("--nodes is required with --db crdb")
        cfg["nodes"] = [ip.strip() for ip in args.nodes.split(",") if ip.strip()]
        cfg["dsn"] = crdb_dsn(cfg["nodes"][0], cfg["database"])

    run_multiprocess(
        cfg, args.rps, args.duration, args.start_batch, args.pool_size,
        args.executor_threads, args.processes, args.sample_rate, args.out,
    )


if __name__ == "__main__":
    main()
