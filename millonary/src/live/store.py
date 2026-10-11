"""Estado persistente del ejecutor (SQLite). Cada barra se procesa en UNA transacción: si el proceso
muere a medias, no queda estado a medias, y reprocesar la misma barra no duplica operaciones."""
from __future__ import annotations
import json, sqlite3
from pathlib import Path


class Store:
    def __init__(self, path: Path):
        path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), isolation_level=None)      # commit manual con BEGIN/COMMIT
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS kv(k TEXT PRIMARY KEY, v TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY AUTOINCREMENT, bar TEXT, side TEXT,
            qty REAL, price REAL, fee REAL, reason TEXT, expo_before REAL, expo_after REAL);
        CREATE TABLE IF NOT EXISTS equity(bar TEXT PRIMARY KEY, equity REAL, units REAL, price REAL,
            expo REAL, signal REAL, target REAL, funding REAL, flags TEXT);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, level TEXT, msg TEXT);
        CREATE TABLE IF NOT EXISTS funding_ledger(time TEXT PRIMARY KEY, rate REAL, units REAL, price REAL, amount REAL,
            synthetic INTEGER);
        """)

    def get(self, k, default=None):
        row = self.db.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
        return json.loads(row[0]) if row else default

    def set(self, k, v):
        self.db.execute("INSERT INTO kv(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, json.dumps(v)))

    def begin(self): self.db.execute("BEGIN IMMEDIATE")            # bloquea a otros escritores (dos procesos)
    def commit(self): self.db.execute("COMMIT")
    def rollback(self): self.db.execute("ROLLBACK")

    def add_trade(self, **t):
        self.db.execute("INSERT INTO trades(bar,side,qty,price,fee,reason,expo_before,expo_after) VALUES(?,?,?,?,?,?,?,?)",
                        (t["bar"], t["side"], t["qty"], t["price"], t["fee"], t["reason"], t["expo_before"], t["expo_after"]))

    def add_equity(self, **e):
        self.db.execute("INSERT OR REPLACE INTO equity VALUES(?,?,?,?,?,?,?,?,?)",
                        (e["bar"], e["equity"], e["units"], e["price"], e["expo"], e["signal"], e["target"],
                         e["funding"], e.get("flags", "")))

    def add_funding(self, time, rate, units, price, amount, synthetic):
        self.db.execute("INSERT OR REPLACE INTO funding_ledger VALUES(?,?,?,?,?,?)",
                        (str(time), float(rate), float(units), float(price), float(amount), int(bool(synthetic))))

    def synthetic_funding(self) -> list:
        cur = self.db.execute("SELECT time, rate, units, price FROM funding_ledger WHERE synthetic=1 ORDER BY time")
        return cur.fetchall()

    def oldest_synthetic_funding(self):
        row = self.db.execute("SELECT MIN(time) FROM funding_ledger WHERE synthetic=1").fetchone()
        return row[0] if row else None

    def log(self, ts, level, msg):
        self.db.execute("INSERT INTO events(ts,level,msg) VALUES(?,?,?)", (ts, level, msg))

    def rows(self, table):
        cur = self.db.execute(f"SELECT * FROM {table}")
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
