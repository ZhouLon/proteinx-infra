from pathlib import Path
import pandas as pd
import numpy as np
from pandas.arrays import StringArray
from typing import Tuple, Optional, Union

def load_table(
        file_path : Path,
        load_mode : dict,
        )->Tuple[Union[StringArray, np.ndarray], Optional[np.ndarray]]:
    
    """
    输入表格型数据，自动读取后返回 可迭代的 成对的 特征和标签
    Args:
        file_path: 文件路径
        load_mode: {
            feature_index: 特征列索引
            label_index: 标签列索引，可选
            header_index: 表头行索引，0表示第一行，None表示无表头
            }
    
    Returns:
        Tuple[Union[StringArray, np.ndarray], Optional[np.ndarray]]:

    """
    feature_index,label_index,header_index=load_mode["feature_index"],load_mode["label_index"],load_mode["header_index"]
    # 限制接受的文件类型
    file_type_list=['.csv','.xlsx']
    file_type = file_path.suffix
    assert file_type in file_type_list
    #限制header类型
    header_type_list=[0,None]
    assert header_index in header_type_list

    if file_type==".csv":
        df = pd.read_csv(file_path,header=header_index)
    elif file_type == ".xlsx":
        df = pd.read_excel(file_path, engine='openpyxl',header=header_index)
    
    feature = df.iloc[:, feature_index].values
    label = None

    if label_index is not None:
        label = df.iloc[:,label_index].values
    
    return feature,label


if __name__ =="__main__":
    file_path=Path("test/data/load_data.xlsx")
    feature,label=load_table(file_path,feature_index=1,label_index=2,header_index=0)
    print(feature,label)