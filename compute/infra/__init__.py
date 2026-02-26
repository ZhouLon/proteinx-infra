

import json
from pathlib import Path  # 路径处理：跨平台、相对结构清晰
import os  
import sys
import importlib.util
import logging
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO, format='[%(name)s] %(levelname)s: %(message)s')


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
    _auto_load_plugins()

def get_workdir():
    """
    从持久化文件读取并返回当前工作目录
    - 读取磁盘中的 config.json，保证与持久化状态一致
    - 若文件缺失或内容异常，上层应做好异常处理（例如首次初始化时使用 set_workdir）
    """
    with CONFIG_PATH.open('r', encoding='utf-8') as f:
        data = json.load(f)
        return Path(data.get('workdir'))

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

def _import_py_modules_from_dir(dir_path: Path, ns_prefix: str):
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        return
    if not dir_path.is_dir():
        return
    for file in dir_path.glob('*.py'):
        if file.name.startswith('_'):
            continue
        spec = importlib.util.spec_from_file_location(f'{ns_prefix}.{file.stem}', str(file))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)

def _auto_load_plugins():
    
    if WORKDIR is None:
        logger.info("工作目录未设置，跳过插件加载。要加载插件，请先运行 infra-wkdir --set <workdir_path>来指定工作目录")
        return
    base = Path(WORKDIR)
    _import_py_modules_from_dir(base / 'model', 'infra_ext.model')
    _import_py_modules_from_dir(base / 'embed', 'infra_ext.embed')
    _import_py_modules_from_dir(base / 'metrics', 'infra_ext.metrics')

_auto_load_plugins()
