from src.data.load_data import load_table
from src.data.embedding.embedding import emb
from src.data.division import divide_data
from pathlib import Path

import torch
from torch import Tensor

if __name__=="__main__":
    
    file_path=Path(r'data\DMS_ProteinGym_substitutions\A0A1I9GEU1_NEIME_Kennouche_2019.csv')
    load_mode={"feature_index":1,"label_index":2,"header_index":0}
    emb_mode='onehot'
    devision_mode={"mode":"ratio","num":"7:1:2","shuffle":True}

    featrue,label=load_table(file_path=file_path,load_mode=load_mode)

    #嵌入
    onehot_featrue:Tensor = emb(featrue,emb_mode)
    label:Tensor = torch.tensor(label,dtype=torch.float32)

    # 数据分集
    featrue_train,featrue_valid,featrue_test=divide_data(onehot_featrue,label,mode=devision_mode)

    
