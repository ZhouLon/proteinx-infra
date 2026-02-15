"""
数据库与查询构造工具（SQLite 元数据）
"""
import os
import sqlite3
import json
from fastapi import HTTPException
from typing import Optional
from app.config import METADATA_DB, METADATA_TABLE

def ensure_metadata_db_exists():
    os.makedirs(os.path.dirname(METADATA_DB), exist_ok=True)
    if not os.path.exists(METADATA_DB):
        conn = sqlite3.connect(METADATA_DB)
        conn.close()

def get_db_conn():
    ensure_metadata_db_exists()
    conn = sqlite3.connect(METADATA_DB)
    conn.row_factory = sqlite3.Row
    return conn

def resolve_table(conn: sqlite3.Connection, table: Optional[str]) -> str:
    if table:
        return table
    if METADATA_TABLE:
        return METADATA_TABLE
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    rows = [r["name"] for r in cur.fetchall()]
    if len(rows) == 1:
        return rows[0]
    if "data_table" in rows:
        return "data_table"
    raise HTTPException(status_code=400, detail="Ambiguous table: please specify table or set METADATA_TABLE")

def build_where_clause(filters: Optional[list], valid_columns: Optional[set] = None) -> (str, list):
    if not filters:
        return "", []
    allowed_ops = {"=", "like", ">", "<", ">=", "<=", "!=", "<>"}
    clauses = []
    params = []
    for f in filters:
        col = f.get("column")
        op = f.get("operator", "=").lower()
        val = f.get("value")
        if not col or op not in allowed_ops:
            continue
        if valid_columns and col not in valid_columns:
            continue
        if op == "like":
            clauses.append(f'"{col}" LIKE ?')
            params.append(f"%{val}%")
        else:
            clauses.append(f'"{col}" {op} ?')
            params.append(val)
    if not clauses:
        return "", []
    return "WHERE " + " AND ".join(clauses), params
