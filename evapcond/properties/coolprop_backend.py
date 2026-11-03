"""CoolProp 后端。全程序只有本模块导入 CoolProp。"""

import math

from evapcond.errors import OutOfRangeError

import CoolProp.CoolProp as CP


class CoolPropBackend:
    """HEOS / HAPropsSI 的薄封装。不在这里改写数值。"""

    def props_si(self, output, name1, value1, name2, value2, fluid):
        value = float(CP.PropsSI(output, name1, value1, name2, value2, fluid))
        return _finite(output, value, "CoolProp PropsSI")

    def ha_props_si(self, output, name1, value1, name2, value2, name3, value3):
        value = float(
            CP.HAPropsSI(output, name1, value1, name2, value2, name3, value3)
        )
        return _finite(output, value, "CoolProp HAPropsSI")

    def version(self):
        return str(CP.get_global_param_string("version"))


def coolprop_version():
    """运行时读到的 CoolProp 版本，供 result.json 使用。"""
    return CoolPropBackend().version()


def _finite(output, value, source):
    if not math.isfinite(value):
        raise OutOfRangeError(output, value, "有限实数", source)
    return value
