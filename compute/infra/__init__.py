"""
infra 包初始化模块

职责：
- 负责“工作目录（WORKDIR）”的全局管理与持久化读取/写入
- 提供 set_workdir/get_workdir/require_workdir API 供运行期使用
- 在包导入时尝试加载已有配置，实现无侵入的默认初始化

设计要点：
- CONFIG_PATH 指向持久化文件（默认：infra/config/config.json）
- WORKDIR 为进程级全局变量，保存当前工作目录的即时值
- 导入时仅尝试加载，不强制失败；真正需要工作目录的地方调用 require_workdir 校验
"""

import json
from pathlib import Path  # 路径处理：跨平台、相对结构清晰
import os  


CONFIG_PATH = Path(__file__).parent / 'config' / 'workdir.json'  # 工作目录配置文件位置


def create_workdir_config():
    """
    尝试从 CONFIG_PATH 读取持久化配置，将 'workdir' 加载到全局 WORKDIR
    - 若文件不存在或解析失败，则保持 WORKDIR=None
    - 在包导入时调用，仅作“最佳努力”初始化，不抛出异常
    """
    global WORKDIR
    if not CONFIG_PATH.exists():
        os.makedirs(CONFIG_PATH.parent, exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump({'workdir': None}, f, ensure_ascii=False)
            WORKDIR = None
    else:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            WORKDIR = data.get('workdir')


def set_workdir(path: str):
    """
    设置当前工作目录并持久化到文件
    - 若路径不存在，会自动创建（与 CLI 行为一致）
    """
    global WORKDIR
    WORKDIR = path
    CONFIG_PATH.write_text(json.dumps({'workdir': WORKDIR}, ensure_ascii=False), encoding='utf-8')

def get_workdir():
    """
    从持久化文件读取并返回当前工作目录
    - 读取磁盘中的 config.json，保证与持久化状态一致
    - 若文件缺失或内容异常，上层应做好异常处理（例如首次初始化时使用 set_workdir）
    """
    with CONFIG_PATH.open('r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('workdir')

def require_workdir():
    """
    强制要求工作目录已设置
    - 若 WORKDIR 为 None，抛出 RuntimeError，提示使用 CLI 设置
    - 推荐在“真正依赖工作目录”的入口函数调用，例如训练入口
    """
    if WORKDIR is None:
        raise RuntimeError("工作目录未设置，请先运行 infra-wkdir --set <workdir_path>来指定工作目录")
    return WORKDIR

create_workdir_config()  # 包导入时执行一次尝试加载
