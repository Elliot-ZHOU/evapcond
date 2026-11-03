"""制冷剂物性。只通过后端调用，流体为 CoolProp HEOS。

R404A、R507A 使用 CoolProp 预定义伪纯质，不调用混合物模型。
饱和温度范围按规格为 −40～+60 °C。R744 的冷凝温度另受 T_crit − 1 K 限制。
单相物性在 −40～+60 °C 内直接计算，含 R744 超临界温度。
"""

from evapcond.errors import InputError, OutOfRangeError
from evapcond.properties.backend import resolve_backend

T_MIN_C = -40.0
T_MAX_C = 60.0

SUPPORTED_REFRIGERANTS = (
    "R717",
    "R22",
    "R134a",
    "R404A",
    "R507A",
    "R744",
)

# CoolProp 中 R404A / R507A 这两个名字是伪纯质状态方程，不是 .mix。
_FLUIDS = {
    "R717": "HEOS::Ammonia",
    "R22": "HEOS::R22",
    "R134a": "HEOS::R134a",
    "R404A": "HEOS::R404A",
    "R507A": "HEOS::R507A",
    "R744": "HEOS::CarbonDioxide",
}

_PSEUDO_PURE = frozenset(("R404A", "R507A"))

R404A_PSEUDOPURE_NOTE = (
    "R404A 按伪纯质计算，温度滑移未计入；若需精确滑移修正，应切换为混合物模型。"
)

_RANGE_SOURCE = "规格：制冷剂饱和温度 −40～+60 °C"
_R744_SOURCE = "R744 在该冷凝温度下不适用蒸发式冷凝"


def coolprop_fluid_name(refrigerant):
    """返回 CoolProp HEOS 流体名。"""
    try:
        return _FLUIDS[refrigerant]
    except KeyError:
        names = "、".join(SUPPORTED_REFRIGERANTS)
        raise InputError(f"未知制冷剂 {refrigerant}。有效值：{names}") from None


def is_pseudo_pure(refrigerant):
    """R404A 与 R507A 为伪纯质。"""
    coolprop_fluid_name(refrigerant)
    return refrigerant in _PSEUDO_PURE


def critical_temperature(refrigerant, backend=None):
    """临界温度，K。"""
    return _trivial(refrigerant, "Tcrit", backend)


def critical_pressure(refrigerant, backend=None):
    """临界压力，Pa。"""
    return _trivial(refrigerant, "Pcrit", backend)


def check_condensing_temperature(refrigerant, T_k, backend=None):
    """检查冷凝温度 T_k（K）。R744 超过 T_crit − 1 K 时终止。"""
    _check_saturation_temperature(
        refrigerant, T_k, backend, param="T_k", as_condensing=True
    )


def saturation_pressure(refrigerant, T, backend=None):
    """饱和压力，Pa。T 为饱和温度，K。"""
    return _sat(refrigerant, T, "P", 0, backend)


def saturation_temperature(refrigerant, p, backend=None):
    """由压力求饱和温度，K。压力须落在允许饱和温度对应的区间内。"""
    t_hi = _max_saturation_temperature(refrigerant, backend)
    p_lo = saturation_pressure(refrigerant, _kelvin(T_MIN_C), backend)
    p_hi = saturation_pressure(refrigerant, t_hi, backend)
    if p < p_lo or p > p_hi:
        raise OutOfRangeError(
            "p",
            p,
            f"[{p_lo}, {p_hi}] Pa",
            _RANGE_SOURCE,
        )
    fluid = coolprop_fluid_name(refrigerant)
    return resolve_backend(backend).props_si("T", "P", p, "Q", 0, fluid)


def liquid_enthalpy(refrigerant, T, backend=None):
    """饱和液焓，J/kg。"""
    return _sat(refrigerant, T, "H", 0, backend)


def vapor_enthalpy(refrigerant, T, backend=None):
    """饱和气焓，J/kg。"""
    return _sat(refrigerant, T, "H", 1, backend)


def liquid_density(refrigerant, T, backend=None):
    """饱和液密度，kg/m³。"""
    return _sat(refrigerant, T, "D", 0, backend)


def vapor_density(refrigerant, T, backend=None):
    """饱和气密度，kg/m³。"""
    return _sat(refrigerant, T, "D", 1, backend)


def liquid_viscosity(refrigerant, T, backend=None):
    """饱和液动力粘度，Pa·s。"""
    return _sat(refrigerant, T, "V", 0, backend)


def vapor_viscosity(refrigerant, T, backend=None):
    """饱和气动力粘度，Pa·s。"""
    return _sat(refrigerant, T, "V", 1, backend)


def liquid_conductivity(refrigerant, T, backend=None):
    """饱和液导热系数，W/(m·K)。"""
    return _sat(refrigerant, T, "L", 0, backend)


def vapor_conductivity(refrigerant, T, backend=None):
    """饱和气导热系数，W/(m·K)。"""
    return _sat(refrigerant, T, "L", 1, backend)


def liquid_cp(refrigerant, T, backend=None):
    """饱和液定压比热，J/(kg·K)。"""
    return _sat(refrigerant, T, "C", 0, backend)


def vapor_cp(refrigerant, T, backend=None):
    """饱和气定压比热，J/(kg·K)。"""
    return _sat(refrigerant, T, "C", 1, backend)


def liquid_prandtl(refrigerant, T, backend=None):
    """饱和液普朗特数。"""
    return _sat(refrigerant, T, "Prandtl", 0, backend)


def vapor_prandtl(refrigerant, T, backend=None):
    """饱和气普朗特数。"""
    return _sat(refrigerant, T, "Prandtl", 1, backend)


def surface_tension(refrigerant, T, backend=None):
    """表面张力，N/m。CoolProp 输出 I。"""
    return _sat(refrigerant, T, "I", 0, backend)


def enthalpy_pt(refrigerant, T, p, backend=None):
    """单相比焓，J/kg。T 为 K，p 为 Pa。"""
    return _single(refrigerant, "H", T, p, backend)


def density_pt(refrigerant, T, p, backend=None):
    """单相密度，kg/m³。"""
    return _single(refrigerant, "D", T, p, backend)


def viscosity_pt(refrigerant, T, p, backend=None):
    """单相动力粘度，Pa·s。"""
    return _single(refrigerant, "V", T, p, backend)


def conductivity_pt(refrigerant, T, p, backend=None):
    """单相导热系数，W/(m·K)。"""
    return _single(refrigerant, "L", T, p, backend)


def cp_pt(refrigerant, T, p, backend=None):
    """单相定压比热，J/(kg·K)。"""
    return _single(refrigerant, "C", T, p, backend)


def prandtl_pt(refrigerant, T, p, backend=None):
    """单相普朗特数。"""
    return _single(refrigerant, "Prandtl", T, p, backend)


def temperature_ph(refrigerant, p, h, backend=None):
    """由压力和比焓求温度，K。结果仍须落在 −40～+60 °C。"""
    saturation_temperature(refrigerant, p, backend)
    fluid = coolprop_fluid_name(refrigerant)
    T = resolve_backend(backend).props_si("T", "P", p, "H", h, fluid)
    _check_single_phase_temperature(T)
    return T


def phase_region(refrigerant, p, h, backend=None):
    """按当地焓与饱和焓判断：subcooled、two_phase 或 superheated。"""
    t_sat = saturation_temperature(refrigerant, p, backend)
    h_f = liquid_enthalpy(refrigerant, t_sat, backend)
    h_g = vapor_enthalpy(refrigerant, t_sat, backend)
    if h < h_f:
        return "subcooled"
    if h > h_g:
        return "superheated"
    return "two_phase"


def vapor_quality(refrigerant, p, h, backend=None):
    """两相区干度。单相时返回 None。"""
    if phase_region(refrigerant, p, h, backend) != "two_phase":
        return None
    t_sat = saturation_temperature(refrigerant, p, backend)
    h_f = liquid_enthalpy(refrigerant, t_sat, backend)
    h_g = vapor_enthalpy(refrigerant, t_sat, backend)
    return (h - h_f) / (h_g - h_f)


def _trivial(refrigerant, output, backend):
    fluid = coolprop_fluid_name(refrigerant)
    return resolve_backend(backend).props_si(output, "", 0, "", 0, fluid)


def _sat(refrigerant, T, output, quality, backend):
    _check_saturation_temperature(refrigerant, T, backend, param="T_sat")
    fluid = coolprop_fluid_name(refrigerant)
    return resolve_backend(backend).props_si(output, "T", T, "Q", quality, fluid)


def _single(refrigerant, output, T, p, backend):
    coolprop_fluid_name(refrigerant)
    _check_single_phase_temperature(T)
    fluid = coolprop_fluid_name(refrigerant)
    return resolve_backend(backend).props_si(output, "T", T, "P", p, fluid)


def _max_saturation_temperature(refrigerant, backend):
    upper = _kelvin(T_MAX_C)
    if refrigerant == "R744":
        upper = min(upper, critical_temperature(refrigerant, backend) - 1.0)
    return upper


def _check_saturation_temperature(refrigerant, T, backend, param, as_condensing=False):
    coolprop_fluid_name(refrigerant)
    if refrigerant == "R744":
        limit = critical_temperature(refrigerant, backend) - 1.0
        if T > limit:
            raise OutOfRangeError(
                "T_k" if as_condensing or param == "T_k" else param,
                T,
                f"<= {limit} K（T_crit - 1 K）",
                _R744_SOURCE,
            )
    if not _in_celsius_interval(T, T_MIN_C, T_MAX_C):
        raise OutOfRangeError(
            param,
            T,
            "−40 °C ～ +60 °C",
            _RANGE_SOURCE,
        )


def _check_single_phase_temperature(T):
    if not _in_celsius_interval(T, T_MIN_C, T_MAX_C):
        raise OutOfRangeError(
            "T",
            T,
            "−40 °C ～ +60 °C",
            "规格：单相物性温度 −40～+60 °C",
        )


def _in_celsius_interval(T, low_c, high_c):
    t_c = T - 273.15
    return (low_c - 1e-9) <= t_c <= (high_c + 1e-9)


def _kelvin(t_c):
    return t_c + 273.15
