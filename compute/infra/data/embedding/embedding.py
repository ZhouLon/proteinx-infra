"""
简易嵌入接口：
- vocab：将序列字符映射到索引张量
- onehot：将索引序列转换为独热编码张量
- emb：统一入口，根据 emb_type_name 路由到具体实现
"""
from torch import Tensor
import torch
from typing import Tuple, Optional, Union, List, Dict
from infra.const import aa_map

def vocab(seq_list: List[str]) -> Tensor:
    """
    将氨基酸序列转换为索引张量（batch x seq_len）
    """
    indexed_seqs = []
    for seq in seq_list:
        indexed_seq = [aa_map[aa] for aa in seq]
        indexed_seqs.append(torch.tensor(indexed_seq))
    return torch.stack(indexed_seqs)

def onehot(seq_list: List[str]) -> Tensor:
    """
    根据 vocab 序列生成独热编码（batch x max_len x vocab_size）
    """
    indexed_seqs = vocab(seq_list)
    vocab_size = len(aa_map)
    max_len = max(len(seq) for seq in seq_list)
    onehot_tensors = []
    for indexed_seq in indexed_seqs:
        onehot_seq = torch.zeros(max_len, vocab_size)
        for i, idx in enumerate(indexed_seq):
            onehot_seq[i, idx] = 1.0
        onehot_tensors.append(onehot_seq)
    return torch.stack(onehot_tensors)

def plm_emb() -> None:
    """
    预留蛋白质语言模型嵌入接口（v1 不实现）
    """
    return None

def emb(seq_list: List[str], emb_type_name: str) -> Union[Tensor, Tuple[Tensor]]:
    """
    嵌入统一入口
    emb_type_name: ['onehot','vocab','esm2']
    """
    emb_type_list = ['onehot', 'vocab', 'esm2']
    assert emb_type_name in emb_type_list, f"嵌入类型必须是 {emb_type_list} 中的一个"
    if emb_type_name == 'onehot':
        return onehot(seq_list)
    elif emb_type_name == 'vocab':
        return vocab(seq_list)
    elif emb_type_name == 'esm2':
        return plm_emb()
    else:
        raise ValueError(f"不支持的嵌入类型: {emb_type_name}")
