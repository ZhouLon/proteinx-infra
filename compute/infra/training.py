from . import get_workdir
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Set, Optional

logger = logging.getLogger(__name__)


def _build_where_clause(filters: List[Dict[str, Any]], valid_cols: Optional[Set[str]] = None) -> (str, list):
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


def _get_db_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", [table])
    return cur.fetchone() is not None

def _get_valid_columns(conn: sqlite3.Connection, table: str) -> Set[str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return {row["name"] for row in cur.fetchall()}


def run_train(
    exp_plan: dict,
    debug: bool = False,
):
    """    
    根据实验计划训练模型
    输入：
        exp_plan: 实验计划字典
        debug: 是否开启调试模式
    输出：
        None"""

    # 解析实验计划
    experiment_id = exp_plan["experiment_id"]
    name = exp_plan["name"]
    local_rank = exp_plan["local_rank"]
    amp = exp_plan["amp"]
    task = exp_plan["task"]
    data = exp_plan["data"]
    embeddings = exp_plan["embeddings"]
    model = exp_plan["model"]
    split = exp_plan["split"]
    train_lr = exp_plan["train.lr"]
    train_batch_size = exp_plan["train.batch_size"]
    train_max_epochs = exp_plan["train.max_epochs"]
    
    WORKDIR = get_workdir()
    DB_PATH = WORKDIR / "data" / "database.db"
    query = exp_plan["data"]["query"]
    
    # 按表分组查询条件
    table_groups: Dict[str, List[Dict[str, Any]]] = {}
    for item in query:
        table_groups.setdefault(item["table"], []).append(item)
    
    rows_by_table: Dict[str, List[sqlite3.Row]] = {}
    
    try:
        conn = _get_db_conn(DB_PATH)
        
        for table, filters in table_groups.items():
            if not _table_exists(conn, table):
                raise RuntimeError(f"training:table_not_found {table}")
            valid_cols = _get_valid_columns(conn, table)
            where_sql, params = _build_where_clause(filters, valid_cols)
            sql = f"SELECT * FROM {table} {where_sql}"
            
            logger.info(f"training:query table={table} where={where_sql} params_count={len(params)}")
            
            cur = conn.execute(sql, params)
            rows_by_table[table] = cur.fetchall()
            
            logger.info(f"training:query_result table={table} rows={len(rows_by_table[table])}")
    except sqlite3.Error as e:
        logger.error(f"training:db_error {e}")
        raise
    finally:
        conn.close()


    # 打印调试信息（仅在debug模式下显示）
    if debug:
        logger.debug("\n=== 数据表信息 ===")
        logger.debug(f"总共读取了 {len(rows_by_table)} 个表")
        
        for table_name, rows in rows_by_table.items():
            logger.debug(f"\n表名: {table_name}")
            logger.debug(f"行数: {len(rows)}")
            
            if rows:
                # 打印前3行的列名和示例数据
                first_row = rows[0]
                columns = list(first_row.keys())
                logger.debug(f"列名: {columns}")
                
                # 打印前3行数据
                logger.debug("前3行数据:")
                for i, row in enumerate(rows[:3]):
                    logger.debug(f"  第{i+1}行: {dict(row)}")
            logger.debug("-" * 50)

    #3 模型训练


    #4 模型评估


    
    #5 训练日志生成
