from torch import Tensor
from torch.utils.data import DataLoader
import torch
from typing import Tuple, Optional, Union, List, Dict
from sklearn.model_selection import train_test_split
import numpy as np



def divide_by_ratio(
    feature: Tensor,
    label: Optional[Tensor] = None,
    ratio: str = "7:1:2",
    random_state: int = 42
) -> dict[Tensor]:
    """
    随机按照指定比例分割数据
    Args:
        feature: 特征张量
        label: 标签张量 (可选)
        ratio: 分割比例字符串
        random_state: 随机种子
    Returns:
        Tuple: 分割后的数据集
    """
    ratios = [float(r) for r in ratio.split(":")]
    ratios = np.array(ratios) / sum(ratios)
    
    if len(ratios) == 3:  # train:val:test
        # 先分割出训练集
        train_size = ratios[0]
        temp_size = ratios[1] + ratios[2]
        
        idx = np.arange(len(feature))
        train_idx, temp_idx = train_test_split(
            idx, test_size=temp_size, random_state=random_state
        )
        
        # 从剩余数据中分割验证集和测试集
        val_ratio = ratios[1] / temp_size
        val_idx, test_idx = train_test_split(
            temp_idx, test_size=1-val_ratio, random_state=random_state
        )
        
        if label is not None:
            return {
            'train': (feature[train_idx], label[train_idx]),
            'valid': (feature[val_idx], label[val_idx]),
            'test': (feature[test_idx], label[test_idx])
            }
        return {
            'train': (feature[train_idx],None),
            'valid': (feature[val_idx],None),
            'test': (feature[test_idx],None)
            }   
    
    else:  # train:test (2个部分)
        train_size = ratios[0]
        
        idx = np.arange(len(feature))
        train_idx, test_idx = train_test_split(
            idx, test_size=1-train_size, random_state=random_state
        )
        
        if label is not None:
            return {
                'train': (feature[train_idx], label[train_idx]),
                'valid': (None,None),
                'test': (feature[test_idx], label[test_idx])
            }
        return {
            'train': (feature[train_idx],None),
            'valid': (None,None),
            'test': (feature[test_idx],None)
}


def divide_by_feature(

) -> dict[Tensor]:
    """
    按照特征值分割数据，策略需要定义
    Args:

    Returns:

    """

    return {'note':"等待完善"}


def divide_by_label(

) -> dict[Tensor]:
    """
    按照标签分割数据,策略需定义
    Args:

    Returns:

    """
    return {'note':"等待完善"}

def create_dataloader(
        data_dict:dict,
        batch_num:dict,
        shuffle:bool
        ) -> dict[Tensor]:
    """
    将分割后的数据转换为DataLoader
    """

    dataloader_dict={}

    batches = [int(r) for r in batch_num["num"].split(":")]
    shuffles = [bool(r) for r in shuffle.split(":")]
    assert len(batches)==len(shuffles)

    if len(batches) == 3:
        batch_dict={"train":batches[0],"valid":batches[1],"test":batches[2]}
        shuffle_dict={"train":shuffles[0],"valid":shuffles[1],"test":shuffles[2]}
    elif len(batches)==2:
        batch_dict={"train":batches[0],"test":batches[1]}
        shuffle_dict={"train":shuffles[0],"test":shuffles[1]}
    else:
        raise ValueError(f"{batches}有问题!")
    
    for key,(feature,label) in data_dict.items():
        
        if feature is None:
            dataloader_dict[key] = None
            continue
            
        if label is not None:
            dataset = MyDataset(feature, label)
        else:
            dataset = MyDataset(feature)
        
        batch_size = batch_dict[key]
        if batch_size == -1:
            batch_size = len(feature)
            
        dataloader = DataLoader(
            dataset, 
            batch_size=batch_size, 
            shuffle=shuffle_dict[key]
        )
        dataloader_dict[key] = dataloader
    
    return dataloader_dict

def divide_data(
    feature: Tensor,
    label: Optional[Tensor] = None,
    batch_num: Dict = {"num": "16:-1:16"},
    mode: Dict = {"mode": "ratio", "num": "7:1:2","shuffle":"1:0:0"}
) -> dict[Tensor]:
    """
    总接口，负责指引具体功能
    Args:
        feature: 特征张量
        label: 标签张量 (可选)
        batch_num: 数据集批次数量,-1代表一次性输入全部数据，
        mode: 分割模式配置字典
    Returns:
        Tuple: 分割后的数据集
    """
    mode_type = mode.get("mode", "ratio")
    
    if mode_type == "ratio":
        ratio = mode.get("num", "7:1:2")
        data_dict=divide_by_ratio(feature, label, ratio=ratio)
        return create_dataloader(data_dict,batch_num,shuffle=mode["shuffle"])
    
    elif mode_type == "feature":

        return divide_by_feature()
    
    elif mode_type == "label":

        return divide_by_label()
    
    else:
        raise ValueError(f"Unknown mode: {mode_type}")


if __name__ == "__main__":
    from infra.data.dataset import MyDataset
    # 测试数据: (nums, seq, emb_dim) = (100, 10, 16)
    np.random.seed(42)
    torch.manual_seed(42)

    # 生成100个样本，每个样本是10x16的序列
    feature = torch.randn(100, 10, 16)
    label = torch.randint(0, 2, (100,))

    print("测试数据形状:")
    print(f"特征: {feature.shape}")
    print(f"标签: {label.shape}")

    # 测试基本功能
    print("\n--- 测试 divide_by_ratio 函数 ---")

    try:
        result = divide_by_ratio(feature, label, ratio="7:1:2")
        print("分割成功!")
        
        # 检查分割后的数据大小
        for split, (feat, lab) in result.items():
            if feat is not None:
                print(f"{split}: 特征 {feat.shape}, 标签 {lab.shape if lab is not None else 'None'}")
    except Exception as e:
        print(f"divide_by_ratio 错误: {e}")

    print("\n--- 测试 divide_data 函数 ---")

    # 测试1: 正常的3分割
    print("\n测试1: 正常的3分割 (7:1:2)")
    try:
        batch_num = {"num": "16:-1:16"}
        mode = {"mode": "ratio", "num": "7:1:2", "shuffle": "1:0:0"}
        
        dataloaders = divide_data(feature, label, batch_num, mode)
        print("divide_data 执行成功!")
        for key, loader in dataloaders.items():
            if loader is not None:
                print(f"{key}: {len(loader.dataset)} 个样本, batch_size={loader.batch_size}")
    except Exception as e:
        print(f"错误: {e}")

    # 测试2: 2分割 (训练:测试)
    print("\n测试2: 2分割 (8:2)")
    try:
        batch_num = {"num": "32:32"}
        mode = {"mode": "ratio", "num": "8:2", "shuffle": "1:0"}
        
        dataloaders = divide_data(feature, label, batch_num, mode)
        print("divide_data 执行成功!")
        for key, loader in dataloaders.items():
            if loader is not None:
                print(f"{key}: {len(loader.dataset)} 个样本, batch_size={loader.batch_size}")
    except Exception as e:
        print(f"错误: {e}")

    # 测试3: 不同的分割比例
    print("\n测试3: 不同的分割比例 (6:2:2)")
    try:
        batch_num = {"num": "8:-1:8"}
        mode = {"mode": "ratio", "num": "6:2:2", "shuffle": "1:1:0"}
        
        dataloaders = divide_data(feature, label, batch_num, mode)
        print("divide_data 执行成功!")
        for key, loader in dataloaders.items():
            if loader is not None:
                print(f"{key}: {len(loader.dataset)} 个样本, batch_size={loader.batch_size}")
    except Exception as e:
        print(f"错误: {e}")

    # 测试4: 不同的batch size设置
    print("\n测试4: 不同的batch size设置")
    try:
        batch_num = {"num": "8:16:32"}  # 不同batch size
        mode = {"mode": "ratio", "num": "7:1:2", "shuffle": "1:1:1"}
        
        dataloaders = divide_data(feature, label, batch_num, mode)
        print("divide_data 执行成功!")
        for key, loader in dataloaders.items():
            if loader is not None:
                print(f"{key}: {len(loader.dataset)} 个样本, batch_size={loader.batch_size}")
    except Exception as e:
        print(f"错误: {e}")

    # 测试5: 全部batch size为-1（完整数据集作为一个batch）
    print("\n测试5: 全部batch size为-1")
    try:
        batch_num = {"num": "-1:-1:-1"}
        mode = {"mode": "ratio", "num": "7:1:2", "shuffle": "0:0:0"}
        
        dataloaders = divide_data(feature, label, batch_num, mode)
        print("divide_data 执行成功!")
        for key, loader in dataloaders.items():
            if loader is not None:
                print(f"{key}: {len(loader.dataset)} 个样本, batch_size={loader.batch_size}")
                # 验证batch数
                batches = list(loader)
                print(f"  -> 共有 {len(batches)} 个batch")
    except Exception as e:
        print(f"错误: {e}")

    # 测试6: 无标签数据
    print("\n测试6: 无标签数据")
    try:
        batch_num = {"num": "16:16"}
        mode = {"mode": "ratio", "num": "8:2", "shuffle": "1:0"}
        
        dataloaders = divide_data(feature, None, batch_num, mode)
        print("divide_data 执行成功!")
        for key, loader in dataloaders.items():
            if loader is not None:
                print(f"{key}: {len(loader.dataset)} 个样本, batch_size={loader.batch_size}")
                # 测试是否可以迭代
                for batch in loader:
                    data = batch
                    if isinstance(data, tuple):
                        print(f"  -> 数据类型: tuple, 元素数量: {len(data)}")
                    else:
                        print(f"  -> 数据类型: {type(data)}")
                    break  # 只查看第一个batch
    except Exception as e:
        print(f"错误: {e}")

    # 测试7: 不同随机种子
    print("\n测试7: 不同随机种子的可重现性")
    try:
        batch_num = {"num": "16:-1:16"}
        mode = {"mode": "ratio", "num": "7:1:2", "shuffle": "1:0:0"}
        
        # 第一次运行
        dataloaders1 = divide_data(feature, label, batch_num, mode)
        indices1 = [loader.dataset.indices.tolist() if hasattr(loader.dataset, 'indices') else 
                   [i for i in range(len(loader.dataset))] for loader in dataloaders1.values() if loader is not None]
        
        # 第二次运行（应该相同）
        dataloaders2 = divide_data(feature, label, batch_num, mode)
        indices2 = [loader.dataset.indices.tolist() if hasattr(loader.dataset, 'indices') else 
                   [i for i in range(len(loader.dataset))] for loader in dataloaders2.values() if loader is not None]
        
        # 比较
        all_same = all(sorted(i1) == sorted(i2) for i1, i2 in zip(indices1, indices2))
        print(f"两次运行分割结果相同: {all_same}")
        
    except Exception as e:
        print(f"错误: {e}")

    # 测试8: 边缘情况测试
    print("\n测试8: 边缘情况测试")
    
    # 测试8.1: 小数据集
    print("\n测试8.1: 小数据集 (10个样本)")
    try:
        small_feature = torch.randn(10, 10, 16)
        small_label = torch.randint(0, 2, (10,))
        
        batch_num = {"num": "4:2:4"}
        mode = {"mode": "ratio", "num": "7:1:2", "shuffle": "1:0:0"}
        
        dataloaders = divide_data(small_feature, small_label, batch_num, mode)
        print("小数据集分割成功!")
        for key, loader in dataloaders.items():
            if loader is not None:
                print(f"{key}: {len(loader.dataset)} 个样本")
    except Exception as e:
        print(f"错误: {e}")
    
    # 测试8.2: 不合理的分割比例
    print("\n测试8.2: 不合理的分割比例 (12:0:-2)")
    try:
        batch_num = {"num": "16:16:16"}
        mode = {"mode": "ratio", "num": "12:0:-2", "shuffle": "1:0:0"}
        dataloaders = divide_data(feature, label, batch_num, mode)
    except Exception as e:
        print(f"预期中的错误: {type(e).__name__}: {e}")

    # 测试9: 检查实际数据内容
    print("\n测试9: 检查数据加载器实际内容")
    try:
        batch_num = {"num": "10:5:5"}
        mode = {"mode": "ratio", "num": "6:2:2", "shuffle": "1:0:0"}
        
        dataloaders = divide_data(feature, label, batch_num, mode)
        
        print("\n检查训练集:")
        train_loader = dataloaders['train']
        for i, batch in enumerate(train_loader):
            if i >= 2:  # 只看前两个batch
                break
            data, target = batch
            print(f"Batch {i+1}: 数据形状={data.shape}, 标签形状={target.shape}")
            print(f"  标签分布: 0={torch.sum(target==0).item()}, 1={torch.sum(target==1).item()}")
        
        print("\n检查验证集:")
        valid_loader = dataloaders['valid']
        if valid_loader is not None:
            for i, batch in enumerate(valid_loader):
                if i >= 1:  # 只看一个batch
                    break
                data, target = batch
                print(f"Batch {i+1}: 数据形状={data.shape}, 标签形状={target.shape}")
    except Exception as e:
        print(f"错误: {e}")

    print("\n--- 所有测试完成 ---")

