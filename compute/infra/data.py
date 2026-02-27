import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Set, Optional, Tuple
import numpy as np
import pandas as pd
import re
from .vocab import get_vocab_processor

logger = logging.getLogger(__name__)

def _get_db_conn(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", [table])
    return cur.fetchone() is not None

def _get_valid_columns(conn: sqlite3.Connection, table: str) -> Set[str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return {row["name"] for row in cur.fetchall()}

def _resolve_table(conn: sqlite3.Connection, table: Optional[str]) -> str:
    if table:
        return table
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    names = [row[0] for row in cur.fetchall()]
    if "mutations" in names:
        return "mutations"
    return names[0] if names else ""

def _build_where_clause(filters: List[Dict[str, Any]], valid_cols: Optional[Set[str]] = None) -> Tuple[str, List[Any]]:
    if not filters:
        return "", []
    allowed_ops = {"=", "like", ">", "<", ">=", "<=", "!=", "<>", "in"}
    clauses = []
    params = []
    for f in filters:
        col = f.get("column")
        op = str(f.get("op", "=")).lower()
        val = f.get("value")
        if not col or op not in allowed_ops:
            continue
        if valid_cols is not None and col not in valid_cols:
            continue
        if op == "in" and isinstance(val, list) and len(val) > 0:
            placeholders = ",".join(["?"] * len(val))
            clauses.append(f'"{col}" IN ({placeholders})')
            params.extend(val)
        elif op == "like":
            clauses.append(f'"{col}" LIKE ?')
            params.append(f"%{val}%")
        else:
            clauses.append(f'"{col}" {op} ?')
            params.append(val)
    if not clauses:
        return "", []
    return "WHERE " + " AND ".join(clauses), params

def query_records(exp_plan: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    db_path = Path(exp_plan.get("data", {}).get("path"))
    dataset = exp_plan.get("data", {}).get("dataset") or {}
    base_filters: List[Dict[str, Any]] = dataset.get("filters") or []
    base_table: Optional[str] = dataset.get("table")
    rows_by_table: Dict[str, List[Dict[str, Any]]] = {}
    conn = _get_db_conn(db_path)
    try:
        real_table = _resolve_table(conn, base_table)
        if not real_table or not _table_exists(conn, real_table):
            raise RuntimeError(f"training:table_not_found {real_table}")
        valid_cols = _get_valid_columns(conn, real_table)
        where_sql, params = _build_where_clause(base_filters, valid_cols)
        join_sources = (real_table == "mutations")
        if join_sources and where_sql:
            where_sql = where_sql.replace('"source"', 's.source_text')
        if join_sources:
            sql = f"SELECT * FROM {real_table} m JOIN sources s ON m.source = s.id {where_sql}"
        else:
            sql = f"SELECT * FROM {real_table} {where_sql}"
        logger.info(f"data.query table={real_table} where={where_sql} params_count={len(params)} params={params}")
        cur = conn.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        rows_by_table[real_table] = rows
        logger.info(f"data.query_result table={real_table} rows={len(rows)}")
        return rows_by_table
    finally:
        conn.close()

def build_dataframe(exp_plan: Dict[str, Any]) -> pd.DataFrame:
    rows_by_table = query_records(exp_plan)
    if not rows_by_table:
        return pd.DataFrame(columns=["id","mutant","DMS_score","DMS_score_bin","mut_num","source","source_text","sequence","sequence_text"])
    real_table = next(iter(rows_by_table.keys()))
    rows = rows_by_table[real_table]
    vocab_name = exp_plan.get("vocab") or "IUPAC"
    proc = get_vocab_processor(vocab_name)
    mut_re = re.compile(r"^([A-Z])(\d+)([A-Z])$")
    seq_text: List[Optional[str]] = []
    for r in rows:
        template = r.get("template")
        mutant = r.get("mutant")
        if not template:
            seq_text.append(None)
            continue
        s = list(str(template))
        ms = str(mutant or "").strip()
        if ms == "" or ms.upper() == "WT":
            seq_text.append("".join(s))
            continue
        parts = ms.split(":")
        for part in parts:
            seg = part.strip()
            if seg == "":
                continue
            m = mut_re.match(seg)
            if not m:
                continue
            _, pos_str, new_aa = m.groups()
            pos = int(pos_str) - 1
            if pos < 0 or pos >= len(s):
                continue
            s[pos] = new_aa
        seq_text.append("".join(s))
    seq_ids: List[np.ndarray] = proc.encode_batch(seq_text)
    df = pd.DataFrame({
        "id": [np.asarray([int(r.get("id"))], dtype=np.int32) if r.get("id") is not None else np.asarray([0], dtype=np.int32) for r in rows],
        "mutant": [str(r.get("mutant")) if r.get("mutant") is not None else None for r in rows],
        "DMS_score": [np.asarray([float(r.get("DMS_score"))], dtype=np.float32) if r.get("DMS_score") is not None else np.asarray([0.0], dtype=np.float32) for r in rows],
        "DMS_score_bin": [str(r.get("DMS_score_bin")) if r.get("DMS_score_bin") is not None else None for r in rows],
        "mut_num": [np.asarray([int(r.get("mut_num"))], dtype=np.int32) if r.get("mut_num") is not None else np.asarray([0], dtype=np.int32) for r in rows],
        "source": [np.asarray([int(r.get("source"))], dtype=np.int32) if r.get("source") is not None else np.asarray([0], dtype=np.int32) for r in rows],
        "source_text": [str(r.get("source_text")) if r.get("source_text") is not None else None for r in rows],
        "sequence": seq_ids,
        "sequence_text": seq_text,
    })
    return df

def log_rows_preview(rows_by_table: Dict[str, List[Dict[str, Any]]]) -> None:
    logger.debug("\n=== 数据表信息 ===")
    logger.debug(f"总共读取了 {len(rows_by_table)} 个表")
    for table_name, rows in rows_by_table.items():
        logger.debug(f"\n表名: {table_name}")
        logger.debug(f"行数: {len(rows)}")
        if rows:
            first_row = rows[0]
            columns = list(first_row.keys())
            logger.debug(f"列名: {columns}")
            logger.debug("前1行数据:")
            for i, row in enumerate(rows[:1]):
                logger.debug(f"  第{i+1}行: {row}")
        logger.debug("-" * 50)
