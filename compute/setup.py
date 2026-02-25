from setuptools import setup, find_packages

setup(
    name="proteinx-infra",
    version="v1",
    packages=find_packages(),
    author="Zhou Long",
    author_email="proteinx@163.com",
    description="AI4Protein infrastructure project v1",
    url="https://proteinx.com.cn",
    entry_points={
        'console_scripts': [
            'infra-train = infra.main:train',  # 训练模型
            'infra-wkdir = infra.main:workdir',  # 工作目录管理
        ]
    },
)
