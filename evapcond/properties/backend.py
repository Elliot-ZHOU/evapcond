"""物性后端接口。求解器只依赖本接口，不依赖具体物性库。"""

from typing import Optional, Protocol


class PropertyBackend(Protocol):
    """制冷剂与水走 PropsSI，湿空气走 HAPropsSI。"""

    def props_si(
        self,
        output: str,
        name1: str,
        value1: float,
        name2: str,
        value2: float,
        fluid: str,
    ) -> float:
        """返回 SI 单位的物性。fluid 使用后端自己的流体名。"""

    def ha_props_si(
        self,
        output: str,
        name1: str,
        value1: float,
        name2: str,
        value2: float,
        name3: str,
        value3: float,
    ) -> float:
        """返回 SI 单位的湿空气物性。"""

    def version(self) -> str:
        """后端库的版本字符串。"""


def resolve_backend(backend: Optional[PropertyBackend]) -> PropertyBackend:
    """每次调用使用传入的后端；未传入时新建一个无可变状态的 CoolProp 后端。"""
    if backend is not None:
        return backend
    from evapcond.properties.coolprop_backend import CoolPropBackend

    return CoolPropBackend()


class CachingBackend:
    """一次求解内部的精确缓存。相同参数返回同一次查询的原值。

    缓存放在这次调用传入的对象上，不作为模块级变量。
    """

    def __init__(self, inner: PropertyBackend):
        self._inner = inner
        self._props = {}
        self._humid = {}

    def props_si(self, output, name1, value1, name2, value2, fluid):
        key = (output, name1, value1, name2, value2, fluid)
        cached = self._props.get(key)
        if cached is not None:
            return cached
        value = self._inner.props_si(output, name1, value1, name2, value2, fluid)
        self._props[key] = value
        return value

    def ha_props_si(self, output, name1, value1, name2, value2, name3, value3):
        key = (output, name1, value1, name2, value2, name3, value3)
        cached = self._humid.get(key)
        if cached is not None:
            return cached
        value = self._inner.ha_props_si(
            output, name1, value1, name2, value2, name3, value3
        )
        self._humid[key] = value
        return value

    def version(self):
        return self._inner.version()


def new_caching_backend():
    """新建一份只在本次求解中使用的 CoolProp 缓存后端。"""
    from evapcond.properties.coolprop_backend import CoolPropBackend

    return CachingBackend(CoolPropBackend())
