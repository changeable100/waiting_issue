"""由数据成员实现配置供给，后端只依赖协议。场景采用精确匹配。"""
import json
from pathlib import Path
from typing import Protocol
from .model import validate_config


class ParameterProvider(Protocol):
    def get_config(self, scenario_id: str) -> dict:
        """返回经审查、带来源信息的 1.0 版配置。"""
        ...


class JsonParameterProvider:
    def __init__(self, registry_path):
        self.path = Path(registry_path).resolve()
        self.registry = json.loads(self.path.read_text(encoding='utf-8'))

    def get_config(self, scenario_id):
        if scenario_id not in self.registry:
            raise ValueError(f'没有匹配参数的场景：{scenario_id}')
        target = (self.path.parent / self.registry[scenario_id]).resolve()
        if not target.is_relative_to(self.path.parent):
            raise ValueError('配置路径不得超出注册表目录')
        config = json.loads(target.read_text(encoding='utf-8'))
        validate_config(config)
        return config
