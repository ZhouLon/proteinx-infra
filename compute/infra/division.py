from typing import Dict, Any
import logging
from .registry import registry

"""
数据划分（Division）使用说明

一、路由与调用
- 在 exp_plan['division'] 中通过 method/type 选择划分方法，当前支持：
  - method='ratio'：按比例随机划分
  - method='mutnum'：按 df['mut_num'] 规则划分
- 入口：train_df, valid_df, test_df = apply_division(df, exp_plan)
- 要求：train/valid/test 三者均不能为空，否则抛错

二、ratio 方法
- 配置：
  {
    "division": {
      "method": "ratio",
      "train": <float>,
      "valid": <float>,
      "test":  <float>
    }
  }
- 约束：
  - 比例和必须等于 1
  - 强制随机（不提供关闭随机的开关）
  - 划分基于打乱后的行索引按比例切片

三、mutnum 方法
- df['mut_num'] 的唯一有序值定义为 uniq_mutnum = sorted(unique(df['mut_num']))
- 选择表达式（字符串）：
  - "[a,b,c]"：选择 mut_num ∈ {a,b,c}
  - "[:k]"：选择 mut_num < k（k 可不在 uniq_mutnum 中，按阈值比较）
  - "[k:]"：选择 mut_num ≥ k（k 可不在 uniq_mutnum 中，按阈值比较）
- 模式：
  1) train/valid/test 均使用显式集合表达式
  2) train/valid 使用显式集合表达式，test 使用 0-1 浮点数：
     - 在 valid 集合对应的样本中，随机选择 (1 - test_float) 作为 test，其余仍作为 valid
- 冲突与覆盖：
  - 若 train/valid/test 的 mut_num 集合发生交叠，不抛错，记录 warning
  - 三者并集可不等于 uniq_mutnum；记录 info：被选择样本数 / 总样本数
"""

class BaseDivision:
    def split(self, df, exp_plan: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

def apply_division(df, exp_plan: Dict[str, Any]):
    logger = logging.getLogger(__name__)
    cfg = exp_plan.get("division") or {}
    method = (cfg.get("method") or cfg.get("type") or "").strip()
    if not method:
        raise RuntimeError("division:method_required")
    cls = registry.get_division(method)
    div = cls()
    splits = div.split(df, exp_plan)
    train_df = splits.get("train")
    valid_df = splits.get("valid")
    test_df = splits.get("test")
    if train_df is None or getattr(train_df, "empty", False):
        raise RuntimeError("division:empty_train")
    if valid_df is None or getattr(valid_df, "empty", False):
        raise RuntimeError("division:empty_valid")
    if test_df is None or getattr(test_df, "empty", False):
        raise RuntimeError("division:empty_test")
    total_rows = len(df)
    n_train = len(train_df)
    n_valid = len(valid_df)
    n_test = len(test_df)
    used_ratio = (n_train + n_valid + n_test) / total_rows if total_rows > 0 else 0.0
    logger.info(f"division:method={method.strip()} total={total_rows} train_rows={n_train} valid_rows={n_valid} test_rows={n_test} used={used_ratio:.4f}")
    mt = method.strip().lower()
    if all(isinstance(cfg.get(k, None), (int, float)) for k in ("train", "valid", "test")):
        tr = float(cfg.get("train"))
        vr = float(cfg.get("valid"))
        rr = float(cfg.get("test"))
        logger.info(f"division:ratio_config train={tr:.6f} valid={vr:.6f} test={rr:.6f}")
    if "mut_num" in getattr(df, "columns", []):
        try:
            uniq = sorted(set(int(x) for x in df["mut_num"].unique().tolist()))
        except Exception:
            uniq = sorted(df["mut_num"].unique().tolist())
        logger.info(f"division:mutnum_unique_sorted {uniq}")
        def _uniq_count(dsub):
            try:
                return len(set(dsub["mut_num"].unique().tolist()))
            except Exception:
                return 0
        c_train = _uniq_count(train_df)
        c_valid = _uniq_count(valid_df)
        c_test = _uniq_count(test_df)
        logger.info(f"division:mutnum_unique_counts train={c_train} valid={c_valid} test={c_test}")
    return train_df, valid_df, test_df
