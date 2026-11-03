"""物性函数入口。求解器与界面通过这些函数取物性，不导入 CoolProp。"""

from evapcond.properties.coolprop_backend import coolprop_version
from evapcond.properties.humid_air import HumidAirState, humid_air_state
from evapcond.properties.refrigerant import (
    R404A_PSEUDOPURE_NOTE,
    SUPPORTED_REFRIGERANTS,
    check_condensing_temperature,
    coolprop_fluid_name,
    is_pseudo_pure,
)
from evapcond.properties.water import latent_heat, surface_tension, vapor_enthalpy

__all__ = [
    "HumidAirState",
    "R404A_PSEUDOPURE_NOTE",
    "SUPPORTED_REFRIGERANTS",
    "check_condensing_temperature",
    "coolprop_fluid_name",
    "coolprop_version",
    "humid_air_state",
    "is_pseudo_pure",
    "latent_heat",
    "surface_tension",
    "vapor_enthalpy",
]
