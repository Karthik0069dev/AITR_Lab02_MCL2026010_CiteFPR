"""SQLite response cache.

Every registry response is stored once, keyed by (source, request key). After the
retrieval pass the cache is frozen (protocol sec. 3): scoring then reads only from the
cache, so every verifier sees identical candidates and a rerun needs no network.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path


class CacheMiss(KeyError):
    pass


class ResponseCache:
    def __init__(self, path: str | Path, frozen: bool = False):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.frozen = frozen
        self.db = sqlite3.connect(str(self.path))
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS resp (source TEXT, key TEXT, status INTEGER, "
            "body TEXT, fetched REAL, PRIMARY KEY (source, key))")
        self.db.commit()

    @staticmethod
    def make_key(params: dict) -> str:
        return json.dumps(params, sort_keys=True, ensure_ascii=False)

    def get(self, source: str, key: str):
        row = self.db.execute("SELECT status, body FROM resp WHERE source=? AND key=?",
                              (source, key)).fetchone()
        if row is None:
            if self.frozen:
                raise CacheMiss(f"{source}:{key}")
            return None
        return row[0], (json.loads(row[1]) if row[1] else None)

    def put(self, source: str, key: str, status: int, body) -> None:
        if self.frozen:
            raise RuntimeError("cache is frozen; refusing to write")
        self.db.execute("INSERT OR REPLACE INTO resp VALUES (?,?,?,?,?)",
                        (source, key, status, json.dumps(body, ensure_ascii=False)
                         if body is not None else None, time.time()))
        self.db.commit()

    def count(self) -> dict:
        return dict(self.db.execute("SELECT source, COUNT(*) FROM resp GROUP BY source").fetchall())

    def close(self) -> None:
        self.db.close()
