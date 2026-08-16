from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv('DATA_DIR') or os.getenv('RAILWAY_VOLUME_MOUNT_PATH') or (ROOT / 'data'))
DB_PATH = DATA_DIR / 'insightflow.db'

SCHEMA = '''
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS researches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  keyword TEXT NOT NULL,
  markets_json TEXT NOT NULL,
  days INTEGER NOT NULL,
  sources_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  progress INTEGER NOT NULL DEFAULT 0,
  message TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  completed_at TEXT
);
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  research_id INTEGER NOT NULL,
  source TEXT NOT NULL,
  market TEXT NOT NULL,
  external_id TEXT,
  title TEXT NOT NULL,
  url TEXT,
  price REAL,
  currency TEXT,
  rating REAL,
  review_count INTEGER,
  seller TEXT,
  badge TEXT,
  thumbnail TEXT,
  raw_json TEXT,
  FOREIGN KEY(research_id) REFERENCES researches(id)
);
CREATE INDEX IF NOT EXISTS idx_products_research ON products(research_id);
CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  research_id INTEGER NOT NULL,
  source TEXT NOT NULL,
  market TEXT NOT NULL,
  product_external_id TEXT,
  product_title TEXT,
  review_external_id TEXT,
  title TEXT,
  text TEXT NOT NULL,
  rating REAL,
  author TEXT,
  review_date TEXT,
  url TEXT,
  helpful INTEGER,
  sentiment TEXT,
  issue TEXT,
  driver TEXT,
  purchase_impact TEXT,
  scenario TEXT,
  FOREIGN KEY(research_id) REFERENCES researches(id)
);
CREATE INDEX IF NOT EXISTS idx_reviews_research ON reviews(research_id);
CREATE INDEX IF NOT EXISTS idx_reviews_issue ON reviews(research_id, issue);
CREATE TABLE IF NOT EXISTS trends (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  research_id INTEGER NOT NULL,
  market TEXT NOT NULL,
  date_label TEXT,
  timestamp INTEGER,
  value REAL,
  FOREIGN KEY(research_id) REFERENCES researches(id)
);
CREATE INDEX IF NOT EXISTS idx_trends_research ON trends(research_id);
'''


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init_db() -> None:
    with conn() as c:
        c.executescript(SCHEMA)


def create_research(keyword: str, markets: list[str], days: int, sources: list[str]) -> int:
    with conn() as c:
        cur = c.execute(
            'INSERT INTO researches(keyword, markets_json, days, sources_json, created_at) VALUES(?,?,?,?,?)',
            (keyword, json.dumps(markets), days, json.dumps(sources), now_iso()),
        )
        return int(cur.lastrowid)


def set_research_status(research_id: int, status: str, progress: int, message: str = '') -> None:
    with conn() as c:
        completed = now_iso() if status in ('completed', 'failed') else None
        c.execute(
            'UPDATE researches SET status=?, progress=?, message=?, completed_at=COALESCE(?, completed_at) WHERE id=?',
            (status, progress, message, completed, research_id),
        )


def get_research(research_id: int):
    with conn() as c:
        r = c.execute('SELECT * FROM researches WHERE id=?', (research_id,)).fetchone()
        return dict(r) if r else None


def list_researches(limit: int = 20):
    with conn() as c:
        rows = c.execute('SELECT * FROM researches ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
        return [dict(x) for x in rows]


def insert_products(research_id: int, rows: Iterable[dict]) -> int:
    n = 0
    with conn() as c:
        for r in rows:
            c.execute('''INSERT INTO products(
              research_id,source,market,external_id,title,url,price,currency,rating,review_count,seller,badge,thumbnail,raw_json
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                research_id, r.get('source',''), r.get('market',''), r.get('external_id'), r.get('title',''), r.get('url'),
                r.get('price'), r.get('currency'), r.get('rating'), r.get('review_count'), r.get('seller'), r.get('badge'),
                r.get('thumbnail'), json.dumps(r.get('raw',{}), ensure_ascii=False)
            ))
            n += 1
    return n


def insert_reviews(research_id: int, rows: Iterable[dict]) -> int:
    n = 0
    with conn() as c:
        for r in rows:
            c.execute('''INSERT INTO reviews(
              research_id,source,market,product_external_id,product_title,review_external_id,title,text,rating,author,review_date,url,helpful,
              sentiment,issue,driver,purchase_impact,scenario
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                research_id, r.get('source',''), r.get('market','GLOBAL'), r.get('product_external_id'), r.get('product_title'),
                r.get('review_external_id'), r.get('title'), r.get('text',''), r.get('rating'), r.get('author'), r.get('review_date'),
                r.get('url'), r.get('helpful'), r.get('sentiment'), r.get('issue'), r.get('driver'), r.get('purchase_impact'), r.get('scenario')
            ))
            n += 1
    return n


def insert_trends(research_id: int, rows: Iterable[dict]) -> int:
    n=0
    with conn() as c:
        for r in rows:
            c.execute('INSERT INTO trends(research_id,market,date_label,timestamp,value) VALUES(?,?,?,?,?)',
                      (research_id,r.get('market',''),r.get('date_label'),r.get('timestamp'),r.get('value')))
            n += 1
    return n


def rows_for(research_id: int, table: str):
    if table not in {'products','reviews','trends'}:
        raise ValueError('bad table')
    with conn() as c:
        rows=c.execute(f'SELECT * FROM {table} WHERE research_id=? ORDER BY id', (research_id,)).fetchall()
        return [dict(x) for x in rows]


def clear_research_data(research_id: int) -> None:
    with conn() as c:
        for t in ('products','reviews','trends'):
            c.execute(f'DELETE FROM {t} WHERE research_id=?', (research_id,))
