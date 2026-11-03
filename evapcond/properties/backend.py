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
