from . import get_workdir
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from .data import build_dataframe
from .embed import apply_embeddings
from .division import apply_division
from .normalize import apply_normalization

logger = logging.getLogger(__name__)


def run_train(
    exp_plan: dict,
    debug: bool = False,
):
    """
    训练主流程
    """
    #从实验计划中获取基本数据
    df = build_dataframe(exp_plan)

    # 归一化（如有配置）
    # df = apply_normalization(df, exp_plan)

    # 对数据进行嵌入
    df = apply_embeddings(df, exp_plan)
    
    # 数据划分
    train_df, valid_df, test_df = apply_division(df, exp_plan)

    
    #3 模型训练


    #4 模型评估


    
    #5 训练日志生成
