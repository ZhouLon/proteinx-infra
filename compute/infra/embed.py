import numpy as np
from typing import List, Optional, Dict, Any
from .vocab import get_vocab_processor
from .registry import registry

class BaseEmbed:
    def embed_sequence_ids_batch(self, seqs: List[np.ndarray], config: Dict[str, Any]) -> List[np.ndarray]:
        raise NotImplementedError
    def embed_sequence_text_batch(self, seqs: List[Optional[str]], config: Dict[str, Any]) -> List[np.ndarray]:
        raise NotImplementedError

def apply_embeddings(df, exp_plan: Dict[str, Any]):
    # 读取实验计划中的嵌入与词表配置，计算词表大小供嵌入使用
    embeds_cfg = exp_plan.get("embeddings")
    vocab_name = exp_plan.get("vocab")
    proc = get_vocab_processor(vocab_name)
    vocab_size = int(len(proc.policy()["id_map"]))
    # 根据 type 选择已注册的嵌入类；无类型时直接返回原始 df
    embed_type = (embeds_cfg.get("type") or "").strip()
    assert vocab_name is not None, "embed:no_vocab_specified"
    assert embeds_cfg is not None, "embed:no_embeddings_specified"
    assert embed_type, "embed:no_type_specified"
    
    embed_cls = registry.get_embed(embed_type)
    caps = getattr(embed_cls, "__embed_capabilities__", {})
    embedder = embed_cls()
    # 合并通用配置，传递 vocab_size 等公共信息给具体嵌入实现
    cfg = dict(embeds_cfg)
    cfg["vocab_size"] = vocab_size
    # 根据能力声明与可用列选择对应接口：优先使用 ids，其次使用 text
    if "sequence" in df.columns and caps.get("ids", False):
        seqs = list(df["sequence"])
        features = embedder.embed_sequence_ids_batch(seqs, cfg)
        df["feature"] = features
    elif "sequence_text" in df.columns and caps.get("text", False):
        seqs = list(df["sequence_text"])
        features = embedder.embed_sequence_text_batch(seqs, cfg)
        df["feature"] = features
    return df
