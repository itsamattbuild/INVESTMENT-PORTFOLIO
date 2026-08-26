
import json, os, sqlite3, sys, time
mode, path, txns_path = sys.argv[1], sys.argv[2], sys.argv[3]
txns = json.load(open(txns_path))

if mode == "json_naive":
    # The obvious implementation: rewrite the whole file in place.
    docs = list(txns)
    docs.append({"id": 501, "ticker": "AAPL", "kind": "buy", "shares": 1.0,
                 "price": 309.9, "split_from": None, "split_to": None,
                 "date": "2026-08-26", "currency": "USD", "commission": 0.0,
                 "note": ""})
    payload = json.dumps({"version": 1, "transactions": docs}, indent=2)
    with open(path, "w") as f:
        step = max(1, len(payload) // 200)
        for i in range(0, len(payload), step):
            f.write(payload[i:i+step])
            f.flush()
            os.fsync(f.fileno())          # force bytes to disk: no cheating
            print("chunk", flush=True)
            time.sleep(0.004)

elif mode == "json_atomic":
    # The safe implementation: temp file, fsync, atomic rename.
    docs = list(txns) + [{"id": 501, "ticker": "AAPL", "kind": "buy",
                          "shares": 1.0, "price": 309.9, "split_from": None,
                          "split_to": None, "date": "2026-08-26",
                          "currency": "USD", "commission": 0.0, "note": ""}]
    tmp = path + ".tmp"
    payload = json.dumps({"version": 1, "transactions": docs}, indent=2)
    with open(tmp, "w") as f:
        step = max(1, len(payload) // 200)
        for i in range(0, len(payload), step):
            f.write(payload[i:i+step])
            f.flush()
            os.fsync(f.fileno())
            print("chunk", flush=True)
            time.sleep(0.004)
    os.replace(tmp, path)
    print("done", flush=True)

elif mode == "sqlite_rows":
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY, ticker TEXT NOT NULL, kind TEXT NOT NULL,
        shares REAL, price REAL, split_from INTEGER, split_to INTEGER,
        date TEXT NOT NULL, currency TEXT NOT NULL DEFAULT 'USD',
        commission REAL NOT NULL DEFAULT 0, note TEXT)""")
    if not con.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]:
        con.executemany("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        [tuple(t[k] for k in ("id","ticker","kind","shares","price",
                                              "split_from","split_to","date",
                                              "currency","commission","note"))
                         for t in txns])
        con.commit()
        print("seeded", flush=True)
    # append one new row, committed on its own -- the normal usage pattern
    time.sleep(0.05)
    con.execute("INSERT INTO transactions VALUES (501,'AAPL','buy',1.0,309.9,"
                "NULL,NULL,'2026-08-26','USD',0.0,'')")
    con.commit()
    print("row", flush=True)

elif mode == "sqlite_bigtxn":
    # worst case for SQLite: everything in ONE transaction, killed halfway
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("CREATE TABLE IF NOT EXISTS transactions ("
                "id INTEGER PRIMARY KEY, ticker TEXT NOT NULL, kind TEXT NOT NULL,"
                "shares REAL, price REAL, split_from INTEGER, split_to INTEGER,"
                "date TEXT NOT NULL, currency TEXT NOT NULL DEFAULT 'USD',"
                "commission REAL NOT NULL DEFAULT 0, note TEXT)")
    con.execute("BEGIN")
    for i, t in enumerate(txns):
        con.execute("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    tuple(t[k] for k in ("id","ticker","kind","shares","price",
                                         "split_from","split_to","date","currency",
                                         "commission","note")))
        if i % 25 == 0:
            print("row", flush=True)
            time.sleep(0.004)
    con.commit()
    print("committed-all", flush=True)
