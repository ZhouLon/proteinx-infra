
from typing import Dict, Type, Callable, Optional, Any
from .model import ProteinModel

"""
统一注册中心（Registry）
作用：
- 在包内部提供一个全局的注册与查询对象 registry
- 管理以下类型的对象：模型（models）、词表（vocabs）、嵌入（embeds）、指标（metrics）、数据划分（divisions）、归一化（normalizations）
- 仅支持“装饰器式注册”，被注册对象均为“类或函数”，查询返回类/可调用（不返回实例）
- 键大小写不敏感，统一归一化为小写
- 重复注册同名键时抛 KeyError

设计要点：
- 与 TAPE 的注册体验保持一致（装饰器/查询），但不引入“任务”概念
- 工作目录插件通过 import 加载模块，模块内使用装饰器完成注册
- 嵌入（embed）注册时允许声明 capabilities（例如 ids/text 接口支持情况）
- division/normalization 不需要能力声明，采用约定的接口方法完成路由

使用示例：
    from infra.registry import registry

    @registry.register_vocab("IUPAC")
    class IUPACProcessor(...):
        ...

    @registry.register_embed("ONEHOT", capabilities={"ids": True, "text": False})
    class OneHotEmbed(...):
        ...

    @registry.register_model("mlp")
    class MLP(...):
        ...

    @registry.register_metric("mse")
    def mean_squared_error(...):
        ...

    @registry.register_division("ratio")
    class RatioDivision(...):
        ...

    @registry.register_normalization("standard")
    class StandardNormalization(...):
        ...

查询示例：
    vocab_cls = registry.get_vocab("iupac")      # 大小写不敏感
    embed_cls = registry.get_embed("onehot")
    model_cls = registry.get_model("mlp")
    metric_fn = registry.get_metric("mse")
    division_cls = registry.get_division("ratio")
    normalization_cls = registry.get_normalization("standard")

异常语义：
- 未注册键：KeyError("registry:<type>_not_found <name>")
- 重复注册：KeyError("registry:<type>_already_exists <name>")
"""

class Registry:
    """
    统一注册与查询的核心类
    - 提供装饰器注册：register_model / register_vocab / register_embed / register_metric
    - 提供查询：get_model / get_vocab / get_embed / get_metric / get_embed_capabilities
    - 内部维护四类映射，均以规范化后的键（小写、去空格）存储
    """
    def __init__(self):
        # 模型类映射：name -> class
        self._models: Dict[str, Type[Any]] = {}
        # 词表类映射：name -> class
        self._vocabs: Dict[str, Type[Any]] = {}
        # 嵌入类映射：name -> class
        self._embeds: Dict[str, Type[Any]] = {}
        # 嵌入能力映射：name -> {"ids": bool, "text": bool}
        self._embed_caps: Dict[str, Dict[str, bool]] = {}
        # 指标函数映射：name -> callable
        self._metrics: Dict[str, Callable] = {}
        # 数据划分类映射：name -> class
        self._divisions: Dict[str, Type[Any]] = {}
        # 归一化类映射：name -> class
        self._normalizations: Dict[str, Type[Any]] = {}

    @staticmethod
    def _norm(name: str) -> str:
        """
        规范化键名：
        - 去除首尾空格
        - 转为小写
        """
        return (name or "").strip().lower()

    # 模型
    def register_model(self, name: str) -> Callable[[Type[Any]], Type[Any]]:
        """
        注册模型类的装饰器
        用法：
            @registry.register_model("mlp")
            class MLP(...): ...
        """
        key = self._norm(name)
        def wrap(cls: Type[Any]) -> Type[Any]:
            if key in self._models:
                raise KeyError(f"registry:model_already_exists {name}")
            self._models[key] = cls
            return cls
        return wrap

    def get_model(self, name: str) -> Type[Any]:
        """
        查询模型类
        返回：模型类（使用者负责实例化）
        """
        key = self._norm(name)
        if key not in self._models:
            raise KeyError(f"registry:model_not_found {name}")
        return self._models[key]

    # 词表
    def register_vocab(self, name: str) -> Callable[[Type[Any]], Type[Any]]:
        """
        注册词表处理类的装饰器
        用法：
            @registry.register_vocab("IUPAC")
            class IUPACProcessor(...): ...
        """
        key = self._norm(name)
        def wrap(cls: Type[Any]) -> Type[Any]:
            if key in self._vocabs:
                raise KeyError(f"registry:vocab_already_exists {name}")
            self._vocabs[key] = cls
            return cls
        return wrap

    def get_vocab(self, name: str) -> Type[Any]:
        """
        查询词表处理类
        返回：词表类（使用者负责实例化）
        """
        key = self._norm(name)
        if key not in self._vocabs:
            raise KeyError(f"registry:vocab_not_found {name}")
        return self._vocabs[key]

    # 嵌入
    def register_embed(self, name: str, capabilities: Optional[Dict[str, bool]] = None) -> Callable[[Type[Any]], Type[Any]]:
        """
        注册嵌入处理类的装饰器
        参数：
            name: 嵌入方法名称
            capabilities: 能力声明字典（可选），目前使用键：
                - "ids": 是否支持基于 ID 序列的接口（df["sequence"]）
                - "text": 是否支持基于文本序列的接口（df["sequence_text"]）
        用法：
            @registry.register_embed("onehot", capabilities={"ids": True, "text": False})
            class OneHotEmbed(...): ...
        """
        key = self._norm(name)
        caps = capabilities or {}
        def wrap(cls: Type[Any]) -> Type[Any]:
            if key in self._embeds:
                raise KeyError(f"registry:embed_already_exists {name}")
            self._embeds[key] = cls
            # 记录能力；缺省为 False
            self._embed_caps[key] = {
                "ids": bool(caps.get("ids", False)),
                "text": bool(caps.get("text", False)),
            }
            # 将能力也写入类属性，便于外部读取
            setattr(cls, "__embed_capabilities__", self._embed_caps[key])
            return cls
        return wrap

    def get_embed(self, name: str) -> Type[Any]:
        """
        查询嵌入处理类
        返回：嵌入类（使用者负责实例化）
        """
        key = self._norm(name)
        if key not in self._embeds:
            raise KeyError(f"registry:embed_not_found {name}")
        return self._embeds[key]

    def get_embed_capabilities(self, name: str) -> Dict[str, bool]:
        """
        查询嵌入能力声明
        返回：{"ids": bool, "text": bool}
        """
        key = self._norm(name)
        if key not in self._embed_caps:
            raise KeyError(f"registry:embed_caps_not_found {name}")
        return self._embed_caps[key]

    # 指标
    def register_metric(self, name: str) -> Callable[[Callable], Callable]:
        """
        注册指标函数的装饰器
        用法：
            @registry.register_metric("mse")
            def mean_squared_error(...): ...
        """
        key = self._norm(name)
        def wrap(fn: Callable) -> Callable:
            if key in self._metrics:
                raise KeyError(f"registry:metric_already_exists {name}")
            self._metrics[key] = fn
            return fn
        return wrap

    def get_metric(self, name: str) -> Callable:
        """
        查询指标函数
        返回：可调用函数
        """
        key = self._norm(name)
        if key not in self._metrics:
            raise KeyError(f"registry:metric_not_found {name}")
        return self._metrics[key]

    # 数据划分
    def register_division(self, name: str) -> Callable[[Type[Any]], Type[Any]]:
        key = self._norm(name)
        def wrap(cls: Type[Any]) -> Type[Any]:
            if key in self._divisions:
                raise KeyError(f"registry:division_already_exists {name}")
            self._divisions[key] = cls
            return cls
        return wrap

    def get_division(self, name: str) -> Type[Any]:
        key = self._norm(name)
        if key not in self._divisions:
            raise KeyError(f"registry:division_not_found {name}")
        return self._divisions[key]

    # 归一化
    def register_normalization(self, name: str) -> Callable[[Type[Any]], Type[Any]]:
        key = self._norm(name)
        def wrap(cls: Type[Any]) -> Type[Any]:
            if key in self._normalizations:
                raise KeyError(f"registry:normalization_already_exists {name}")
            self._normalizations[key] = cls
            return cls
        return wrap

    def get_normalization(self, name: str) -> Type[Any]:
        key = self._norm(name)
        if key not in self._normalizations:
            raise KeyError(f"registry:normalization_not_found {name}")
        return self._normalizations[key]

# 全局唯一注册对象；包内与工作目录插件统一使用该对象进行注册与查询
registry = Registry()
