from typing import Dict, Any
from .registry import registry

"""
归一化（Normalization）模块
目标：
- 在训练流水线中提供一个可插拔的归一化步骤
- 接收并返回 DataFrame（df），保持与上游/下游一致的接口形态
- 采用统一注册中心 + 装饰器注册的方式加载具体归一化实现

使用方式：
- 在工作目录中定义归一化类，并使用 registry.register_normalization("name") 完成注册
- 在 flags/exp_plan 中通过 normalization.method 或 normalization.type 指定名称进行路由
- 当未配置归一化时，apply_normalization 直接返回原始 df

配置示例（加入到 exp_plan 中）：
    "normalization": {
        "method": "standard",
        "scope": "global"
    }
说明：
- method/type：选择具体的归一化实现名称（大小写不敏感）
- 其他键由具体归一化类自行解释，例如 scope/input/列名等
"""

class BaseNormalization:
    """
    归一化的基类
    约定：
    - fit(df, exp_plan)：拟合归一化所需的统计量或状态（如均值/方差），可选择不做任何操作
    - transform(df, exp_plan)：基于拟合状态对 df 进行变换并返回新的 df
    - 具体归一化实现需定义目标列或数据域的处理方式（feature/label/指定列）
    """
    def fit(self, df, exp_plan: Dict[str, Any]) -> Any:
        raise NotImplementedError
    def transform(self, df, exp_plan: Dict[str, Any]):
        raise NotImplementedError

def apply_normalization(df, exp_plan: Dict[str, Any]):
    """
    归一化入口：
    - 读取 exp_plan["normalization"] 配置，解析 method/type
    - 未配置或未指定名称时，直接返回原始 df
    - 已配置时，从注册中心查询归一化类，执行 fit 与 transform 并返回结果
    """
    cfg = exp_plan.get("normalization") or {}
    method = (cfg.get("method") or cfg.get("type") or "").strip()
    if not method:
        # 未指定归一化，原样透传
        return df
    # 查询并实例化归一化类
    cls = registry.get_normalization(method)
    norm = cls()
    # 先拟合，再变换
    norm.fit(df, exp_plan)
    return norm.transform(df, exp_plan)
