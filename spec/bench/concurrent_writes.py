"""Two processes writing the same data file -- what actually happens."""

import json
import os
import sqlite3
import subprocess
import sys
import time

WRITER = r'''
import json, sqlite3, sys, time
mode, path, tag = sys.argv[1], sys.argv[2], sys.argv[3]
if mode == "sqlite":
    con = sqlite3.connect(path, timeout=3.0)   # 3s busy_timeout like a patient app
    con.execute("PRAGMA busy_timeout=3000")
    for i in range(20):
        con.execute("INSERT INTO events VALUES (?,?)", (f"{tag}-{i}", tag))
        con.commit()
        time.sleep(0.01)
elif mode == "json":
    # the natural pattern: read whole file, append, rewrite whole file
    for i in range(20):
        try:
            doc = json.load(open(path))
        except Exception:
            doc = {"log": []}
        doc["log"].append(f"{tag}-{i}")
        with open(path, "w") as f:
            json.dump(doc, f)
        time.sleep(0.01)
'''

open("/tmp/opencode/life/writer.py", "w").write(WRITER)

print("=== JSON: two processes, interleaved read-modify-write ===")
p = "/tmp/opencode/life/clobber.json"
json.dump({"log": []}, open(p, "w"))
procs = [subprocess.Popen([sys.executable, "/tmp/opencode/life/writer.py",
                           "json", p, tag]) for tag in ("proc-A", "proc-B")]
for pr in procs:
    pr.wait()
final = json.load(open(p))["log"]
a = sum(1 for x in final if x.startswith("proc-A"))
b = sum(1 for x in final if x.startswith("proc-B"))
print(f"A wrote 20 lines, B wrote 20 lines; final log has {len(final)} entries "
      f"(A: {a}, B: {b})")
print("lost entries:", 40 - len(final), "-- last writer wins, earlier writers silently erased")

print()
print("=== SQLite: two processes, row-at-a-time, WAL mode ===")
p = "/tmp/opencode/life/locked.db"
if os.path.exists(p):
    os.remove(p)
con = sqlite3.connect(p)
con.execute("PRAGMA journal_mode=WAL")
con.execute("CREATE TABLE events (k TEXT, tag TEXT)")
con.commit()
con.close()
procs = [subprocess.Popen([sys.executable, "/tmp/opencode/life/writer.py",
                           "sqlite", p, tag], stderr=subprocess.PIPE, text=True)
         for tag in ("proc-A", "proc-B")]
errs = []
for pr in procs:
    _, err = pr.communicate()
    if err:
        errs.append(err.strip().splitlines()[-1])
con = sqlite3.connect(p)
n_a = con.execute("SELECT COUNT(*) FROM events WHERE tag='proc-A'").fetchone()[0]
n_b = con.execute("SELECT COUNT(*) FROM events WHERE tag='proc-B'").fetchone()[0]
ic = con.execute("PRAGMA integrity_check").fetchone()[0]
con.close()
print(f"A inserted {n_a}/20 rows, B inserted {n_b}/20 rows; integrity_check={ic}")
print("errors:", errs or "none -- WAL + busy_timeout serialises the writers")

print()
print("=== same test without busy_timeout (default 5s? no -- default is 0 wait via timeout param) ===")
W2 = WRITER.replace('timeout=3.0', 'timeout=0.1')
open("/tmp/opencode/life/writer2.py", "w").write(W2)
p = "/tmp/opencode/life/locked2.db"
if os.path.exists(p):
    os.remove(p)
con = sqlite3.connect(p)
con.execute("PRAGMA journal_mode=WAL")
con.execute("CREATE TABLE events (k TEXT, tag TEXT)")
con.commit(); con.close()
procs = [subprocess.Popen([sys.executable, "/tmp/opencode/life/writer2.py",
                           "sqlite", p, tag], stderr=subprocess.PIPE, text=True)
         for tag in ("proc-A", "proc-B")]
errs = []
for pr in procs:
    _, err = pr.communicate()
    if err:
        errs.append(err.strip().splitlines()[-1][:60])
con = sqlite3.connect(p)
n_a = con.execute("SELECT COUNT(*) FROM events WHERE tag='proc-A'").fetchone()[0]
n_b = con.execute("SELECT COUNT(*) FROM events WHERE tag='proc-B'").fetchone()[0]
con.close()
print(f"A inserted {n_a}/20, B inserted {n_b}/20; errors seen:")
for e in errs[:3]:
    print("  ", e)
