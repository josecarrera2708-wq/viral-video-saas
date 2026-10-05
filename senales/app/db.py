"""Base de datos SQLite (un único fichero en la carpeta de datos)."""
import json
import os
import sqlite3
import threading

DATA = os.environ.get("SENALES_DATA", "/opt/senales/data")
os.makedirs(DATA, exist_ok=True)
_conn = sqlite3.connect(os.path.join(DATA, "senales.db"), check_same_thread=False, timeout=60)
_conn.execute("pragma journal_mode=wal")
_conn.row_factory = sqlite3.Row
_lock = threading.Lock()

SCHEMA = """
create table if not exists meta(k text primary key, v text);
create table if not exists sessions(token text primary key, exp integer);
create table if not exists wallets(addr text primary key, name text, rank integer, origin text,
    note text, payers text default '[]', active integer default 1, added integer);
create table if not exists trades(sig text, wallet text, mint text, side text, t integer, amount real,
    usd real, sol real, price real, mc real, sym text, entry real, primary key(sig, wallet, mint));
create table if not exists positions(wallet text, mint text, sym text, icon text, first_t integer,
    entry_price real, entry_mc real, usd_in real, usd_out real default 0, max_price real, max_t integer,
    last_price real, last_t integer, supply real, bf integer, primary key(wallet, mint));
create table if not exists seen(sig text primary key, t integer);
create table if not exists subs(endpoint text primary key, data text, added integer);
create table if not exists candidates(addr text primary key, origin text, found integer, score real,
    n integer, pct_x2 real, ladder real, all_x2 real, avg_xmax real, hits integer, detail text, status text default 'nueva');
create table if not exists scan_tokens(mint text primary key, sym text, exch text, t_list integer, done integer, buyers integer);
"""
with _lock:
    _conn.executescript(SCHEMA)
    if "bf" not in [r[1] for r in _conn.execute("pragma table_info(positions)")]:
        _conn.execute("alter table positions add column bf integer")
    if "entry" not in [r[1] for r in _conn.execute("pragma table_info(trades)")]:
        # en las ventas: precio medio al que había comprado (null = por buscar, 0 = no se encontró la compra)
        _conn.execute("alter table trades add column entry real")
    _conn.commit()


def q(sql, args=(), one=False):
    with _lock:
        cur = _conn.execute(sql, args)
        rows = cur.fetchall()
    rows = [dict(r) for r in rows]
    return (rows[0] if rows else None) if one else rows


def x(sql, args=()):
    with _lock:
        _conn.execute(sql, args)
        _conn.commit()


def xm(sql, seq):
    with _lock:
        _conn.executemany(sql, seq)
        _conn.commit()


def get(k, default=None):
    r = q("select v from meta where k=?", (k,), one=True)
    return json.loads(r["v"]) if r else default


def put(k, v):
    x("insert into meta(k, v) values(?, ?) on conflict(k) do update set v=excluded.v", (k, json.dumps(v)))
