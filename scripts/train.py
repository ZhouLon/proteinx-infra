from src.data.load_data import load_table
from src.data.embedding
from pathlib import Path


if __name__=="__main__":
    file_path=Path(r'data\DMS_ProteinGym_substitutions\A0A1I9GEU1_NEIME_Kennouche_2019.csv')
    featrue,label=load_table(file_path=file_path,feature_index=1,label_index=2,header_index=0)

    嵌入


    
