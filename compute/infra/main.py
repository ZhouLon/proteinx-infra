import typing
import os
import logging
from .parser import InfraParser
import argparse
import inspect
from .training import run_train
from . import set_workdir, get_workdir, require_workdir
logger = logging.getLogger(__name__)



def train(args: typing.Optional[argparse.Namespace] = None)->None:
    if args is None:
        parser = InfraParser()
        args = parser.args
        arg_dict = parser.arg_dict
    require_workdir()
    
    arg_names = inspect.getfullargspec(run_train).args

    missing = set(arg_names) - set(arg_dict.keys())
    if missing:
        raise RuntimeError(f"Missing arguments: {missing}")
    train_args = {name: arg_dict[name] for name in arg_names}
    run_train(**train_args)
    

def workdir(args: typing.Optional[argparse.Namespace] = None) -> None:
    parser = argparse.ArgumentParser(description='Infra 工作目录管理')
    parser.add_argument('--get', action='store_true')
    parser.add_argument('--set', type=str, default=None)
    parser.add_argument('--clear', action='store_true')
    parsed = parser.parse_args() if args is None else args
    if parsed.clear:
        set_workdir(None)  
        print("已清空工作目录")
        return
    if parsed.set is not None:
        p = os.path.abspath(parsed.set)
        os.makedirs(p, exist_ok=True)
        set_workdir(p)
        print(f"已设置工作目录: {p}")
        return
    if parsed.get:
        wd = get_workdir()
        print(f"当前工作目录: {wd}")
        return
    print("使用 --get 查询，或 --set <path> 设置，或 --clear 清空")

if __name__ == "__main__":
    pass
    pass
