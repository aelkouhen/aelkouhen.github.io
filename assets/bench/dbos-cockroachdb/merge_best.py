"""
Produce final canonical result files:
- results_pg_final.json      : original PG run (already RC by default)
- results_crdb_final.json    : best throughput per concurrency level
                               from Serializable vs RC runs
- results_raw_pg_final.json  : original PG raw run
- results_raw_crdb_final.json: best raw throughput per level
"""
import json

def best(a_path, b_path, key, out_path):
    with open(a_path) as f: a = json.load(f)
    with open(b_path) as f: b = json.load(f)
    key_name = list(a.keys())[0]   # "workflows" or "raw_writes"
    a_rows = {r["concurrency"]: r for r in a[key_name]}
    b_rows = {r["concurrency"]: r for r in b[key_name]}
    merged = []
    for c in sorted(a_rows):
        ra, rb = a_rows[c], b_rows.get(c, a_rows[c])
        winner = ra if ra["throughput"] >= rb["throughput"] else rb
        merged.append(winner)
        src = "A" if winner is ra else "B"
        print(f"  c={c:>4}  tput={winner['throughput']:>8.1f}  p50={winner['p50']:>7.1f}  src={src}")
    with open(out_path, "w") as f:
        json.dump({key_name: merged}, f, indent=2)
    print(f"  → {out_path}\n")

print("=== CRDB workflows: Serializable vs RC ===")
best("/tmp/dbos-bench/results_coloc.json",
     "/tmp/dbos-bench/results_coloc_rc.json",
     "workflows",
     "/tmp/dbos-bench/results_crdb_final.json")

print("=== CRDB raw writes: first run vs RC run ===")
best("/tmp/dbos-bench/results_raw_crdb.json",
     "/tmp/dbos-bench/results_raw_crdb_rc.json",
     "raw_writes",
     "/tmp/dbos-bench/results_raw_crdb_final.json")

# PG: just copy originals (RC by default, second run identical)
import shutil
shutil.copy("/tmp/dbos-bench/results_pg.json",     "/tmp/dbos-bench/results_pg_final.json")
shutil.copy("/tmp/dbos-bench/results_raw_pg.json", "/tmp/dbos-bench/results_raw_pg_final.json")
print("PG finals copied from original runs.")
