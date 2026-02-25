import argparse
import os
import json



class InfraParser:
    def __init__(self):
        self.infra_parser = argparse.ArgumentParser(description='Parent parser for infra',add_help=False)
        self._init_parser()
        # 解析参数
        add_args = self.infra_parser.parse_args()
        plan_args = self._read_exp_plan(add_args.exp_plan_path)
        # 合并参数
        self.args = self._merge_args(add_args, plan_args)
        # 检查参数是否合法
        self.args = self._check_parser(self.args)
        # 转换为字典
        self.arg_dict = vars(self.args)

    def _read_exp_plan(self, exp_plan: str):
        """读取实验计划文件"""
        with open(exp_plan, 'r') as f:
            exp_plan = json.load(f)
            
        return {"exp_plan": exp_plan}

    def _merge_args(self, args: argparse.Namespace, plan: dict) -> argparse.Namespace:
        for k, v in plan.items():
            if not hasattr(args, k) or getattr(args, k) is None:
                setattr(args, k, v)
        return args

    def _init_parser(self):
        #必须的参数
        self.infra_parser.add_argument('exp_plan_path',type=str, help='实验的计划路径')

        # 可选的参数
        self.infra_parser.add_argument('--debug',type=bool, default=False, help='是否开启debug模式')

    def _check_parser(self, args: argparse.Namespace):
        # 先检查是否存在 exp_plan 属性
        if not hasattr(args, 'exp_plan'):
            raise ValueError("exp_plan is required")
        # 再检查 exp_plan 中是否存在 data 和 model
        if args.exp_plan.get('data',None) is None:
            raise ValueError("data is required")
        if args.exp_plan.get('model',None) is None:
            raise ValueError("model is required")

        return args
        
    
