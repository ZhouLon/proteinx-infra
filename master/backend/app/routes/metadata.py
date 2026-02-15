"""
元数据路由（SQLite）
"""
import json
import sqlite3
import logging
from fastapi import APIRouter, HTTPException
from typing import Optional
from app.utils.db import get_db_conn, resolve_table, build_where_clause
import time
import os
from app.config import METADATA_DEFAULT_PAGE_SIZE, METADATA_MAX_PAGE_SIZE, METADATA_DB

router = APIRouter(prefix="/api/metadata", tags=["metadata"])

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
        cols = [{"cid": row["cid"], "name": row["name"], "type": row["type"], "notnull": row["notnull"], "pk": row["pk"]} for row in cur.fetchall()]
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
        # 空查询采用常量复杂度分页：按主键/ID/rowid的区间检索，而非 OFFSET
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
            data_sql = f"{select_prefix} FROM {real_table} {where_sql} {order_clause} LIMIT ? OFFSET ?"
            t10 = time.perf_counter()
            cur = conn.execute(data_sql, params + [effective_page_size, offset])
            rows = [dict(row) for row in cur.fetchall()]
        duration_ms = int((time.perf_counter() - t0) * 1000)
        logging.info(f"metadata_query:data_select_ms={int((time.perf_counter() - t10)*1000)} order_clause=\"{order_clause}\" range_mode={range_mode}")
        logging.info(f"metadata_query:done total_ms={duration_ms}")
        return {"page": page, "per_page": effective_page_size, "total": total, "rows": rows, "duration_ms": duration_ms, "total_source": total_source}
    except sqlite3.OperationalError as e:
        logging.error(f"metadata_query OperationalError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
