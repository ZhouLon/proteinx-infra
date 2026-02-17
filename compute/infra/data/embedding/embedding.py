from torch import Tensor
import torch
import pandas as pd
from pandas.arrays import StringArray
from infra.const import aa_map

from typing import Tuple, Optional, Union, List, Dict
import numpy as np

def vocab(
        seq_list: List[str]
        ) -> Tensor:
    """
    生成词汇表索引
    
    Args:
        seq_list: 字符串序列列表
        
    Returns:
        tuple: (词汇表字典, 索引序列列表)
    """
    
    # 将序列转换为索引
    indexed_seqs = []
    for seq in seq_list:
        indexed_seq = [aa_map[aa] for aa in seq]
        indexed_seqs.append(torch.tensor(indexed_seq))
    
    return  torch.stack(indexed_seqs)

def onehot(
        seq_list: List[str]
        ) -> Tensor:
    """
    生成独热编码
    
    Args:
        seq_list: 字符串序列列表
        
    Returns:
        Tensor: 独热编码张量，形状为 (batch_size, seq_len, vocab_size)
    """
    # 获取词汇表
    indexed_seqs = vocab(seq_list)
    vocab_size = len(aa_map)
    
    # 找到最大序列长度
    max_len = max(len(seq) for seq in seq_list)
    
    # 创建独热编码张量
    onehot_tensors = []
    for indexed_seq in indexed_seqs:
        onehot_seq = torch.zeros(max_len, vocab_size)
        for i, idx in enumerate(indexed_seq):
            onehot_seq[i, idx] = 1.0
        
        onehot_tensors.append(onehot_seq)
    
    # 堆叠所有序列
    return torch.stack(onehot_tensors)

def plm_emb() -> None:
    """
    蛋白质语言模型嵌入，指引到...（v1版本不补充）
    
    Returns:
        None
    """
    return None

def emb(
        seq_list: List[str], 
        emb_type_name: str
        ) -> Union[Tensor,Tuple[Tensor]]:
    """
    最外层的接口，负责指引
    
    Args:
        seq_list: 字符串序列列表
        emb_type_name: 嵌入类型名称
        
    Returns:
        根据嵌入类型返回相应的表示
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

if __name__ == "__main__":
    # 测试数据
    test_seqs = ["ACDE", "FGHI", "KLMN"]
    
    # 测试 vocab 函数
    print("测试 vocab 函数:")
    indexed_seqs = vocab(test_seqs)
    print(f"索引序列: {indexed_seqs}")
    print()
    
    # 测试 onehot 函数
    print("测试 onehot 函数:")
    onehot_tensor = onehot(test_seqs)
    print(f"独热编码形状: {onehot_tensor.shape}")
    print(f"独热编码数据类型: {onehot_tensor.dtype}")
    print()
    
    # 测试 emb 接口
    print("测试 emb 接口:")
    
    # 测试 onehot 嵌入
    onehot_result = emb(test_seqs, 'onehot')
    print(f"onehot 嵌入结果形状: {onehot_result}")
    
    # 测试 vocab 嵌入
    vocab_result = emb(test_seqs, 'vocab')
    indexed_seqs_result = vocab_result
    print(f"vocab 嵌入词汇表大小: {indexed_seqs_result}")
    
    # 测试 esm2 嵌入
    esm2_result = emb(test_seqs, 'esm2')
    print(f"esm2 嵌入结果: {esm2_result}")