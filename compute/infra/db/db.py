"""
SQLite 元数据库访问与查询构造模块：
- MetaDB：连接与查询封装
- QueryBuilder：对 sources/mutations 表的白名单条件构造
- select_dataset(flags)：根据 flags.data.query 生成联合查询并返回 DataFrame
"""
from pathlib import Path
import sqlite3
import pandas as pd
from typing import Any, Dict, List, Tuple, Union
from infra.config import metadata_db_path

class MetaDB:
    """
    元数据库连接封装，默认使用工作目录下的 /metadata/database.db
    """
    def __init__(self, db_path: Union[str, Path] = None):
        self.db_path = Path(db_path) if db_path else metadata_db_path()
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """关闭连接"""
        self.conn.close()

    def query(self, sql: str, params: Tuple[Any, ...] = ()) -> pd.DataFrame:
        """执行只读查询并返回 DataFrame"""
        return pd.read_sql_query(sql, self.conn, params=params)

class QueryBuilder:
    """
    查询条件构造器：
    - 白名单列与操作符校验，避免 SQL 注入
    - 构造 sources/mutations 的联合查询 where 子句
    """
    def __init__(self):
        self.allowed_cols_sources = {"id", "source_text", "template"}
        self.allowed_cols_mutations = {"id", "mutant", "DMS_score", "DMS_score_bin", "mut_num", "source"}
        self.allowed_ops = {"=", "!=", ">", ">=", "<", "<=", "IN"}

    def build_where(self, conditions: List[Dict[str, Any]]) -> Tuple[str, List[Any]]:
        """
        根据条件列表构造安全的 where 子句与绑定参数
        条件示例：{table: "mutations", column: "DMS_score_bin", op: "IN", value: ["A","B"]}
        """
        clauses = []
        params: List[Any] = []
        for cond in conditions:
            table = cond.get("table")
            col = cond.get("column")
            op = cond.get("op")
            val = cond.get("value")
            if table == "sources" and col in self.allowed_cols_sources and op in self.allowed_ops:
                if op == "IN" and isinstance(val, list):
                    placeholders = ",".join(["?"] * len(val))
                    clauses.append(f"s.{col} IN ({placeholders})")
                    params.extend(val)
                else:
                    clauses.append(f"s.{col} {op} ?")
                    params.append(val)
            elif table == "mutations" and col in self.allowed_cols_mutations and op in self.allowed_ops:
                if op == "IN" and isinstance(val, list):
                    placeholders = ",".join(["?"] * len(val))
                    clauses.append(f"m.{col} IN ({placeholders})")
                    params.extend(val)
                else:
                    clauses.append(f"m.{col} {op} ?")
                    params.append(val)
        where_sql = ""
        if clauses:
            where_sql = " WHERE " + " AND ".join(clauses)
        return where_sql, params

    def build_query(self, conditions: List[Dict[str, Any]]) -> Tuple[str, List[Any]]:
        """构造联合查询 SQL 与参数"""
        where_sql, params = self.build_where(conditions)
        sql = (
            "SELECT m.id AS mutation_id, m.mutant, m.DMS_score, m.DMS_score_bin, m.mut_num, "
            "s.id AS source_id, s.source_text, s.template "
            "FROM mutations m JOIN sources s ON m.source = s.id" + where_sql
        )
        return sql, params

def select_dataset(flags: Dict[str, Any]) -> pd.DataFrame:
    """
    按 flags['data.query'] 进行查询，返回 DataFrame
    """
    qb = QueryBuilder()
    conds = flags.get("data.query", [])
    sql, params = qb.build_query(conds if isinstance(conds, list) else [])
    db = MetaDB()
    df = db.query(sql, tuple(params))
    db.close()
    return df
