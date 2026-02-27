"""
元数据路由（SQLite）
"""
import json
import sqlite3
import logging
import re
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any, List
from app.utils.db import get_db_conn, resolve_table, build_where_clause
import time
import os
from app.config import METADATA_DEFAULT_PAGE_SIZE, METADATA_MAX_PAGE_SIZE, METADATA_DB, MUTATIONS_TABLE, SOURCES_TABLE, MUTATION_REGEX

router = APIRouter(prefix="/api/metadata", tags=["metadata"])

_MUTATION_PATTERN = re.compile(MUTATION_REGEX)
_SOURCES_CACHE: Dict[str, Any] = {"fingerprint": None, "data": None}

def _get_db_fingerprint() -> Optional[float]:
    # 使用数据库文件修改时间作为轻量指纹，避免频繁全表查询
    try:
        return os.path.getmtime(METADATA_DB)
    except Exception:
        return None

def _load_sources_cache(conn: sqlite3.Connection, force_refresh: bool = False) -> Dict[int, Dict[str, str]]:
    # source 表很小，缓存到内存以避免每次查询都访问数据库
    fingerprint = _get_db_fingerprint()
    cache = _SOURCES_CACHE.get("data")
    if cache is not None and _SOURCES_CACHE.get("fingerprint") == fingerprint and not force_refresh:
        return cache
    try:
        cur = conn.execute(f"SELECT id, source_text, template FROM {SOURCES_TABLE}")
        data = {
            row["id"]: {
                "source_text": row["source_text"],
                "template": row["template"],
            }
            for row in cur.fetchall()
        }
        _SOURCES_CACHE["data"] = data
        _SOURCES_CACHE["fingerprint"] = fingerprint
        return data
    except sqlite3.OperationalError as e:
        logging.warning(f"metadata_query:source_cache_load_error err={e}")
        _SOURCES_CACHE["data"] = {}
        _SOURCES_CACHE["fingerprint"] = fingerprint
        return _SOURCES_CACHE["data"]

def _apply_mutations_to_template(template: Optional[str], mutant: Optional[str]) -> Optional[str]:
    # 根据模板序列与突变描述生成最终序列，突变格式形如 A673E:A692E
    if not template:
        return None
    if not mutant:
        return template
    mutant_str = str(mutant).strip()
    if mutant_str == "" or mutant_str.upper() == "WT":
        return template
    seq = list(template)
    for part in mutant_str.split(":"):
        segment = part.strip()
        if segment == "":
            continue
        match = _MUTATION_PATTERN.match(segment)
        if not match:
            logging.warning(f"metadata_query:mutation_parse_fail mutant={segment}")
            continue
        original_aa, pos_str, new_aa = match.groups()
        pos = int(pos_str) - 1
        if pos < 0 or pos >= len(seq):
            logging.warning(f"metadata_query:mutation_out_of_range mutant={segment} pos={pos}")
            continue
        if seq[pos] != original_aa:
            logging.warning(f"metadata_query:mutation_mismatch mutant={segment} template={seq[pos]}")
        seq[pos] = new_aa
    return "".join(seq)

@router.get("/tables")
def metadata_tables():
    conn = get_db_conn()
    try:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row["name"] for row in cur.fetchall()]
        return {"tables": tables}
    finally:
        conn.close()

@router.get("/columns")
def metadata_columns(table: Optional[str] = None):
    conn = get_db_conn()
    try:
        real_table = resolve_table(conn, table)
        cur = conn.execute(f"PRAGMA table_info({real_table})")
        pragma_rows = cur.fetchall()
        cols_by_name = {row["name"]: row for row in pragma_rows}
        if real_table == MUTATIONS_TABLE:
            # mutations 表需要扩展 sequence 与映射后的 source，保证展示顺序稳定
            has_mut_num = "mut_num" in cols_by_name
            ordered_cols = ["id", "mutant"] + (["mut_num"] if has_mut_num else []) + ["DMS_score", "DMS_score_bin", "sequence", "source"]
            cols: List[Dict[str, Any]] = []
            for idx, name in enumerate(ordered_cols):
                if name == "sequence":
                    cols.append({"cid": idx, "name": "sequence", "type": "TEXT", "notnull": 0, "pk": 0})
                    continue
                row = cols_by_name.get(name)
                if row is None:
                    continue
                col_type = row["type"]
                if name == "source":
                    col_type = "TEXT"
                cols.append({"cid": idx, "name": name, "type": col_type, "notnull": row["notnull"], "pk": row["pk"]})
            return {"columns": cols}
        cols = [{"cid": row["cid"], "name": row["name"], "type": row["type"], "notnull": row["notnull"], "pk": row["pk"]} for row in pragma_rows]
        return {"columns": cols}
    finally:
        conn.close()

@router.get("/query")
def metadata_query(table: Optional[str] = None, page: int = 1, per_page: int = METADATA_DEFAULT_PAGE_SIZE, pageSize: Optional[int] = None, filters: Optional[str] = None):
    effective_page_size = pageSize if pageSize is not None else per_page
    if effective_page_size < 1:
        effective_page_size = METADATA_DEFAULT_PAGE_SIZE
    if effective_page_size > METADATA_MAX_PAGE_SIZE:
        effective_page_size = METADATA_MAX_PAGE_SIZE
    if page < 1:
        raise HTTPException(status_code=400, detail="Invalid pagination")
    filters_obj = None
    if filters:
        try:
            filters_obj = json.loads(filters)
            print(1,table, filters_obj)
            if not isinstance(filters_obj, list):
                filters_obj = None
        except Exception:
            filters_obj = None
    where_sql, params = "", []
    offset = (page - 1) * effective_page_size
    t0 = time.perf_counter()
    logging.info(f"metadata_query:start page={page} pageSize={effective_page_size} offset={offset} filters_count={0 if not filters_obj else len(filters_obj)}")
    t1 = time.perf_counter()
    conn = get_db_conn()
    try:
        t2 = time.perf_counter()
        logging.info(f"metadata_query:conn_open_ms={int((t2 - t1)*1000)}")
        t3 = time.perf_counter()
        real_table = resolve_table(conn, table)
        t4 = time.perf_counter()
        logging.info(f"metadata_query:resolve_table_ms={int((t4 - t3)*1000)} table={real_table}")
        t5 = time.perf_counter()
        cur = conn.execute(f"PRAGMA table_info({real_table})")
        pragma_rows = cur.fetchall()
        valid_cols = {row["name"] for row in pragma_rows}
        pk_col = None
        for row in pragma_rows:
            if row["pk"]:
                pk_col = row["name"]
                break
        t6 = time.perf_counter()
        where_sql, params = build_where_clause(filters_obj, valid_cols)
        join_sources = False
        if real_table == MUTATIONS_TABLE and filters_obj:
            for f in (filters_obj or []):
                if f.get("column") == "source":
                    join_sources = True
                    break
        if join_sources and where_sql:
            where_sql = where_sql.replace('"source"', 's.source_text')
        t7 = time.perf_counter()
        logging.info(f"metadata_query:build_where_ms={int((t7 - t6)*1000)} where_empty={1 if (not where_sql or where_sql.strip()=='') else 0}")
        is_empty_query = (not filters_obj) or (where_sql.strip() == "")
        # 计数逻辑（空查询采用缓存，首次无缓存时计算并缓存；缓存校验指纹避免过时）
        total_source = "db"
        meta_dir = os.path.dirname(METADATA_DB)
        os.makedirs(meta_dir, exist_ok=True)
        cache_path = os.path.join(meta_dir, f"{real_table}.count.json")
        total = None
        # 构造数据库变更指纹（轻量）：文件修改时间 + page_count + freelist_count
        db_mtime = None
        try:
            db_mtime = os.path.getmtime(METADATA_DB)
        except Exception:
            db_mtime = None
        fp_page_count = None
        fp_freelist_count = None
        try:
            fp_page_count = conn.execute("PRAGMA page_count").fetchone()[0]
            fp_freelist_count = conn.execute("PRAGMA freelist_count").fetchone()[0]
        except Exception:
            pass
        current_fingerprint = {
            "mtime": db_mtime,
            "page_count": fp_page_count,
            "freelist_count": fp_freelist_count
        }
        if is_empty_query:
            try:
                if os.path.exists(cache_path):
                    with open(cache_path, "r", encoding="utf-8") as f:
                        cache = json.load(f)
                    cached_total = cache.get("total")
                    cached_fp = cache.get("fingerprint") or {}
                    if isinstance(cached_total, int) and cached_total >= 0 and cached_fp == current_fingerprint:
                        total = cached_total
                        total_source = "cache"
                        logging.info(f"metadata_query:count_cache_hit total={total} fingerprint_ok=1")
                    else:
                        logging.info("metadata_query:count_cache_miss fingerprint_changed=1")
            except Exception as e:
                logging.warning(f"metadata_query:count_cache_read_error err={e}")
        if total is None:
            if real_table == MUTATIONS_TABLE and not is_empty_query and join_sources:
                count_sql = f"SELECT COUNT(*) as cnt FROM {real_table} m JOIN {SOURCES_TABLE} s ON m.source = s.id {where_sql}"
            else:
                count_sql = f"SELECT COUNT(*) as cnt FROM {real_table} {where_sql}"
            t8 = time.perf_counter()
            cur = conn.execute(count_sql, params)
            total = cur.fetchone()["cnt"]
            t9 = time.perf_counter()
            logging.info(f"metadata_query:count_ms={int((t9 - t8)*1000)} total={total}")
            if is_empty_query:
                try:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump({
                            "table": real_table,
                            "total": total,
                            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "fingerprint": current_fingerprint
                        }, f, ensure_ascii=False, indent=2)
                    total_source = "db_write_cache"
                    logging.info(f"metadata_query:count_cache_write total={total} path={cache_path} fingerprint_saved=1")
                except Exception as e:
                    logging.warning(f"metadata_query:count_cache_write_error err={e}")
        order_clause = ""
        if is_empty_query:
            if pk_col:
                order_clause = f'ORDER BY "{pk_col}" ASC'
            elif "id" in valid_cols:
                order_clause = 'ORDER BY "id" ASC'
            else:
                order_clause = "ORDER BY rowid ASC"
        select_prefix = "SELECT *"
        if is_empty_query and not pk_col and "id" not in valid_cols:
            select_prefix = "SELECT rowid as __rowid__, *"
        # 空查询采用常量复杂度分页：按主键/ID/rowid的区间检索
        range_mode = 0
        if is_empty_query:
            key_field = pk_col if pk_col else ("id" if "id" in valid_cols else "rowid")
            start_id = (page - 1) * effective_page_size + 1
            end_id = start_id + effective_page_size - 1
            if isinstance(total, int) and total >= 0:
                if end_id > total:
                    end_id = total
            select_prefix_range = select_prefix
            if key_field == "rowid" and (not pk_col) and ("id" not in valid_cols):
                select_prefix_range = "SELECT rowid as __rowid__, *"
            data_sql = f"{select_prefix_range} FROM {real_table} WHERE {key_field} BETWEEN ? AND ? ORDER BY {key_field} ASC"
            t10 = time.perf_counter()
            cur = conn.execute(data_sql, [start_id, end_id])
            rows = [dict(row) for row in cur.fetchall()]
            range_mode = 1
            logging.info(f"metadata_query:range_mode=1 key_field={key_field} start_id={start_id} end_id={end_id}")
        else:
            if real_table == MUTATIONS_TABLE and join_sources:
                data_sql = f"{select_prefix} FROM {real_table} m JOIN {SOURCES_TABLE} s ON m.source = s.id {where_sql} {order_clause} LIMIT ? OFFSET ?"
            else:
                data_sql = f"{select_prefix} FROM {real_table} {where_sql} {order_clause} LIMIT ? OFFSET ?"
            t10 = time.perf_counter()
            cur = conn.execute(data_sql, params + [effective_page_size, offset])
            rows = [dict(row) for row in cur.fetchall()]
        if real_table == MUTATIONS_TABLE:
            # mutations 表输出需要额外映射与序列生成，确保前端无需再处理
            sources_cache = _load_sources_cache(conn)
            cache_refreshed = False
            mapped_rows: List[Dict[str, Any]] = []
            for row in rows:
                source_id = row.get("source")
                source_entry = sources_cache.get(source_id)
                if source_entry is None and source_id is not None and not cache_refreshed:
                    sources_cache = _load_sources_cache(conn, force_refresh=True)
                    cache_refreshed = True
                    source_entry = sources_cache.get(source_id)
                source_text = source_entry.get("source_text") if source_entry else None
                template = source_entry.get("template") if source_entry else None
                sequence = _apply_mutations_to_template(template, row.get("mutant"))
                mapped_rows.append({
                    "id": row.get("id"),
                    "mutant": row.get("mutant"),
                    "mut_num": row.get("mut_num"),
                    "DMS_score": row.get("DMS_score"),
                    "DMS_score_bin": row.get("DMS_score_bin"),
                    "sequence": sequence,
                    "source": source_text,
                })
            rows = mapped_rows
        duration_ms = int((time.perf_counter() - t0) * 1000)
        logging.info(f"metadata_query:data_select_ms={int((time.perf_counter() - t10)*1000)} order_clause=\"{order_clause}\" range_mode={range_mode}")
        logging.info(f"metadata_query:done total_ms={duration_ms}")
        return {"page": page, "per_page": effective_page_size, "total": total, "rows": rows, "duration_ms": duration_ms, "total_source": total_source}
    except sqlite3.OperationalError as e:
        logging.error(f"metadata_query OperationalError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
