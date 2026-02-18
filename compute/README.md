
ProteinX Infra Compute

是一个算力资源。完成任务后可以把信息同步到master节点。

使用方法
1.可以配置好包后直接ssh到节点上使用


目标
网络管理
    信息传输（和master节点通信）



数据：
    数据加载
        1 从文件加载
        2 从数据库加载
    数据清洗
    数据嵌入
    数据分集

模型管理
根据tag直接加载插入到代码

训练

评估方法

实验规划：需要和master节点协调，确定共同结构。

实验记录


conda create -n proteinx_infra_compute python=3.12

conda activate proteinx_infra_compute

pip install -r requirements.txt

pip install -e .




