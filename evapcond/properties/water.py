"""水物性。CoolProp HEOS，表面张力用 PropsSI 的 I（IAPWS）。

规格范围：5～60 °C。液态物性默认压力 101325 Pa，且不得低于该温度的饱和压力。
"""

from evapcond.errors import OutOfRangeError
from evapcond.properties.backend import resolve_backend

T_MIN_C = 5.0
T_MAX_C = 60.0
P_DEFAULT = 101325.0
_FLUID = "HEOS::Water"
_SOURCE = "规格：水 5～60 °C"


def density(T, p=P_DEFAULT, backend=None):
    """液态密度，kg/m³。"""
    return _liquid(T, p, "D", backend)


def specific_heat(T, p=P_DEFAULT, backend=None):
    """液态定压比热，J/(kg·K)。"""
    return _liquid(T, p, "C", backend)


def viscosity(T, p=P_DEFAULT, backend=None):
    """液态动力粘度，Pa·s。"""
    return _liquid(T, p, "V", backend)


def conductivity(T, p=P_DEFAULT, backend=None):
    """液态导热系数，W/(m·K)。"""
    return _liquid(T, p, "L", backend)


def enthalpy(T, p=P_DEFAULT, backend=None):
    """液态比焓，J/kg。"""
    return _liquid(T, p, "H", backend)


def surface_tension(T, backend=None):
    """表面张力，N/m。PropsSI 输出 I。"""
    _check_temperature(T)
    return resolve_backend(backend).props_si("I", "T", T, "Q", 0, _FLUID)


def saturation_pressure(T, backend=None):
    """饱和压力，Pa。"""
    _check_temperature(T)
    return resolve_backend(backend).props_si("P", "T", T, "Q", 0, _FLUID)


def liquid_enthalpy_sat(T, backend=None):
    """饱和液焓，J/kg。"""
    _check_temperature(T)
    return resolve_backend(backend).props_si("H", "T", T, "Q", 0, _FLUID)


def vapor_enthalpy(T, backend=None):
    """饱和水蒸气焓 i_g，J/kg。参考态为 CoolProp HEOS。"""
    _check_temperature(T)
    return resolve_backend(backend).props_si("H", "T", T, "Q", 1, _FLUID)


def latent_heat(T, backend=None):
    """汽化潜热 h_fg，J/kg。"""
    return vapor_enthalpy(T, backend) - liquid_enthalpy_sat(T, backend)


def _liquid(T, p, output, backend):
    _check_temperature(T)
    backend = resolve_backend(backend)
    p_sat = backend.props_si("P", "T", T, "Q", 0, _FLUID)
    if p < p_sat:
        raise OutOfRangeError(
            "p",
            p,
            f">= {p_sat} Pa",
            "液态水压力不得低于饱和压力",
        )
    return backend.props_si(output, "T", T, "P", p, _FLUID)


def _check_temperature(T):
    t_c = T - 273.15
    if t_c < T_MIN_C - 1e-9 or t_c > T_MAX_C + 1e-9:
        raise OutOfRangeError("T", T, "5 °C ～ 60 °C", _SOURCE)
