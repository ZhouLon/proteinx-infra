
from typing import Dict, Type, Callable
from .model import ProteinModel

#通过registry来管理嵌入，模型，指标

class ModelSpec:
    """
    name (str):
        The name of the task
    models (Dict[str, ProteinModel]):
        The set of models that can be used for this task. Default: {}.
    """

    def __init__(self,
                 name: str,
                 models: Dict[str, Type[ProteinModel]] = None):
        self.name = name
        self.models = models if models is not None else {}

    def register_model(self, model_name: str, model_cls: Type[ProteinModel] = None):
        if model_cls is not None:
            if model_name in self.models:
                raise KeyError(
                    f"A model with name '{model_name}' is already registered for this task")
            self.models[model_name] = model_cls
            return model_cls
        else:
            return lambda model_cls: self.register_model(model_name, model_cls)

    def get_model(self, model_name: str) -> Type[ProteinModel]:
        # 获取某任务下注册的模型类
        return self.models[model_name]

class Registry:
    r"""Class for registry object which acts as the
    central repository for TAPE."""

    model_name_mapping: Dict[str, Callable] = {}
    metric_name_mapping: Dict[str, Callable] = {}
    models : Dict[str, Type[ProteinModel]] = {}
