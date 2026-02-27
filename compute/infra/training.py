from . import get_workdir
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from .data import query_records, build_dataframe, log_rows_preview

logger = logging.getLogger(__name__)


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
    
    rows_by_table: Dict[str, List[Dict[str, Any]]] = query_records(exp_plan)
    df = build_dataframe(exp_plan)
    
    # 打印调试信息
    log_rows_preview(rows_by_table)

    #3 模型训练
    logger.info(f"dataframe:rows {df.shape[0]} cols {list(df.columns)}")
    try:
        preview = df.head(10).to_dict(orient="records")
        logger.debug(f"dataframe:preview_first10 {preview}")
    except Exception as e:
        logger.debug(f"dataframe:preview_error {e}")


    #4 模型评估


    
    #5 训练日志生成
