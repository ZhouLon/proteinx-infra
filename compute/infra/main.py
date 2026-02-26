import typing
import os
import logging
from .parser import TrainParser, WorkdirParser
import argparse
import inspect
from .training import run_train
from . import set_workdir, get_workdir, require_workdir
logger = logging.getLogger(__name__)

# 配置基础日志格式，针对所有脚本
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)



def train(args: typing.Optional[argparse.Namespace] = None)->None:
    if args is None:
        parser = TrainParser()
        args = parser.args
        arg_dict = parser.arg_dict

    # 设置全局日志级别
    if arg_dict.get('debug', False):
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("=== 调试模式已启用 ===")
    else:
        logging.getLogger().setLevel(logging.INFO)

    #确保工作目录有加载
    require_workdir()
    
    arg_names = inspect.getfullargspec(run_train).args

    missing = set(arg_names) - set(arg_dict.keys())
    if missing:
        raise RuntimeError(f"Missing arguments: {missing}")
    train_args = {name: arg_dict[name] for name in arg_names}
    run_train(**train_args)
    

def workdir(args: typing.Optional[argparse.Namespace] = None) -> None:
    if args is None:
        parser = WorkdirParser()
        args = parser.args
        arg_dict = parser.arg_dict

    if arg_dict.get('clear'):
        set_workdir(None)
        logger.info("已清空工作目录")
        return
    if arg_dict.get('set') is not None:
        p = os.path.abspath(arg_dict['set'])
        os.makedirs(p, exist_ok=True)
        set_workdir(p)
        logger.info(f"已设置工作目录: {p}")
        return
    if arg_dict.get('get'):
        wd = get_workdir()
        logger.info(f"当前工作目录: {wd}")
        return
    if not arg_dict.get('help'):
        logger.info("使用 --get 查询，或 --set <path> 设置，或 --clear 清空")

if __name__ == "__main__":
    pass

