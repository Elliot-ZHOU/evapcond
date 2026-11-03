"""制冷剂侧一个控制容积：区段、热阻、换热量和出口压力。

区段按当地焓与当地饱和焓划分。饱和温度每次都由当地压力重算。
0 ≤ x < 1 用 Shah。x = 1 以及过热、过冷用 Gnielinski。压降为摩擦项加均相加速项。
"""

import math
from dataclasses import dataclass

from evapcond.correlations.condensation import shah_condensation_coefficient
from evapcond.correlations.pressure_drop import (
    acceleration_pressure_drop,
    friedel_friction_gradient,
    homogeneous_specific_volume,
    single_phase_friction_gradient,
)
from evapcond.correlations.single_phase import gnielinski_coefficient
from evapcond.errors import InputError, OutOfRangeError
from evapcond.properties.refrigerant import (
    conductivity_pt,
    critical_pressure,
    density_pt,
    liquid_conductivity,
    liquid_density,
    liquid_prandtl,
    liquid_viscosity,
    phase_region,
    prandtl_pt,
    saturation_temperature,
    surface_tension,
    temperature_ph,
    vapor_conductivity,
    vapor_density,
    vapor_prandtl,
    vapor_quality,
    vapor_viscosity,
    viscosity_pt,
)

# CoolProp 拒绝落在饱和线上的 (T, p) 单相查询。温差不超过此值时改用饱和相物性。
_SATURATION_FLASH_BAND_K = 1.0e-4


@dataclass(frozen=True)
class RefrigerantState:
    """当地压力下的制冷剂状态。T_sat 由该压力求出。"""

    p: float
    h: float
    T: float
    T_sat: float
    region: str
    x: float | None


@dataclass(frozen=True)
class RefrigerantSegment:
    """一个管段的制冷剂侧结果。压力单位 Pa，焓单位 J/kg。"""

    state_in: RefrigerantState
    state_out: RefrigerantState
    h_ref: float
    G: float
    dQ_ref: float
    R_ref: float
    R_wall: float
    R_film: float
    dp_fric: float
    dp_acc: float
    warnings: tuple
    correlations: tuple


def refrigerant_state(refrigerant, p, h, backend=None):
    """用当地压力更新饱和温度，再按焓判断过热、两相或过冷。"""
    t_sat = saturation_temperature(refrigerant, p, backend)
    region = phase_region(refrigerant, p, h, backend)
    quality = vapor_quality(refrigerant, p, h, backend)
    if region == "two_phase":
        temperature = t_sat
    else:
        temperature = temperature_ph(refrigerant, p, h, backend)
    return RefrigerantState(
        p=p,
        h=h,
        T=temperature,
        T_sat=t_sat,
        region=region,
        x=quality,
    )


def wall_resistance(d_o, d_i, k_w, dL):
    """R_wall = ln(d_o/d_i) / (2 π k_w dL)，K/W。"""
    _positive("d_o", d_o)
    _positive("d_i", d_i)
    _positive("k_w", k_w)
    _positive("dL", dL)
    if d_o <= d_i:
        raise OutOfRangeError("d_o/d_i", d_o / d_i, "> 1", "管壁热阻")
    return math.log(d_o / d_i) / (2.0 * math.pi * k_w * dL)


def evaluate_refrigerant_segment(
    refrigerant, d_i, d_o, k_w, dL, m_dot, p, h, T_w, R_film, backend=None
):
    """沿流动方向推进一个控制容积。出口饱和温度对应当地出口压力。"""
    if not math.isfinite(m_dot) or m_dot <= 0.0:
        raise InputError("制冷剂流量必须大于 0")
    _positive("d_i", d_i)
    _positive("dL", dL)
    if not math.isfinite(T_w):
        raise OutOfRangeError("T_w", T_w, "有限温度", "制冷剂侧")
    if not math.isfinite(R_film) or R_film < 0.0:
        raise OutOfRangeError("R_film", R_film, "≥ 0 K/W", "水膜热阻")
    state_in = refrigerant_state(refrigerant, p, h, backend)
    area_i = math.pi * d_i * dL
    g = m_dot / (math.pi * d_i**2 / 4.0)
    h_ref, heat_warnings, heat_records = _heat_transfer_coefficient(
        refrigerant, state_in, g, d_i, backend
    )
    r_ref = 1.0 / (h_ref * area_i)
    r_wall = wall_resistance(d_o, d_i, k_w, dL)
    dQ = (state_in.T - T_w) / (r_ref + r_wall + R_film)
    if not math.isfinite(dQ):
        raise OutOfRangeError("dQ_ref", dQ, "有限值", "制冷剂侧能量")
    h_out = h - dQ / m_dot
    dp_fric, friction_record = _friction_drop(
        refrigerant, state_in, g, d_i, dL, backend
    )
    v_in = _specific_volume(refrigerant, state_in, backend)
    frozen = refrigerant_state(refrigerant, p, h_out, backend)
    v_out = _specific_volume(refrigerant, frozen, backend)
    dp_acc, accel_record = acceleration_pressure_drop(g, v_in, v_out)
    p_out = p - dp_fric - dp_acc
    state_out = refrigerant_state(refrigerant, p_out, h_out, backend)
    return RefrigerantSegment(
        state_in=state_in,
        state_out=state_out,
        h_ref=h_ref,
        G=g,
        dQ_ref=dQ,
        R_ref=r_ref,
        R_wall=r_wall,
        R_film=R_film,
        dp_fric=dp_fric,
        dp_acc=dp_acc,
        warnings=heat_warnings,
        correlations=heat_records + (friction_record, accel_record),
    )


def _heat_transfer_coefficient(refrigerant, state, G, d_i, backend):
    if state.region == "two_phase" and state.x is not None and state.x < 1.0:
        mu_l = liquid_viscosity(refrigerant, state.T_sat, backend)
        pr_l = liquid_prandtl(refrigerant, state.T_sat, backend)
        k_l = liquid_conductivity(refrigerant, state.T_sat, backend)
        p_crit = critical_pressure(refrigerant, backend)
        value, record, warnings = shah_condensation_coefficient(
            G, d_i, state.x, state.p, p_crit, mu_l, pr_l, k_l
        )
        return value, warnings, (record,)
    if state.region == "superheated" or state.x == 1.0:
        mu, pr, k = _vapor_transport(refrigerant, state, backend)
    else:
        mu, pr, k = _liquid_transport(refrigerant, state, backend)
    value, record, warnings = gnielinski_coefficient(G, d_i, mu, pr, k)
    return value, warnings, (record,)


def _friction_drop(refrigerant, state, G, d_i, dL, backend):
    if state.region == "two_phase":
        rho_l = liquid_density(refrigerant, state.T_sat, backend)
        rho_g = vapor_density(refrigerant, state.T_sat, backend)
        mu_l = liquid_viscosity(refrigerant, state.T_sat, backend)
        mu_g = vapor_viscosity(refrigerant, state.T_sat, backend)
        sigma = surface_tension(refrigerant, state.T_sat, backend)
        gradient, record = friedel_friction_gradient(
            G, d_i, state.x, rho_l, rho_g, mu_l, mu_g, sigma
        )
    else:
        rho, mu = _single_phase_density_viscosity(refrigerant, state, backend)
        gradient, record = single_phase_friction_gradient(G, d_i, rho, mu)
    return gradient * dL, record


def _specific_volume(refrigerant, state, backend):
    if state.region == "two_phase":
        rho_l = liquid_density(refrigerant, state.T_sat, backend)
        rho_g = vapor_density(refrigerant, state.T_sat, backend)
        return homogeneous_specific_volume(state.x, rho_l, rho_g)
    rho, _ = _single_phase_density_viscosity(refrigerant, state, backend)
    return 1.0 / rho


def _liquid_transport(refrigerant, state, backend):
    if state.region == "two_phase" or _on_saturation_line(state):
        return (
            liquid_viscosity(refrigerant, state.T_sat, backend),
            liquid_prandtl(refrigerant, state.T_sat, backend),
            liquid_conductivity(refrigerant, state.T_sat, backend),
        )
    return (
        viscosity_pt(refrigerant, state.T, state.p, backend),
        prandtl_pt(refrigerant, state.T, state.p, backend),
        conductivity_pt(refrigerant, state.T, state.p, backend),
    )


def _vapor_transport(refrigerant, state, backend):
    if state.region == "two_phase" or _on_saturation_line(state):
        return (
            vapor_viscosity(refrigerant, state.T_sat, backend),
            vapor_prandtl(refrigerant, state.T_sat, backend),
            vapor_conductivity(refrigerant, state.T_sat, backend),
        )
    return (
        viscosity_pt(refrigerant, state.T, state.p, backend),
        prandtl_pt(refrigerant, state.T, state.p, backend),
        conductivity_pt(refrigerant, state.T, state.p, backend),
    )


def _single_phase_density_viscosity(refrigerant, state, backend):
    if _on_saturation_line(state):
        if state.region == "superheated":
            return (
                vapor_density(refrigerant, state.T_sat, backend),
                vapor_viscosity(refrigerant, state.T_sat, backend),
            )
        return (
            liquid_density(refrigerant, state.T_sat, backend),
            liquid_viscosity(refrigerant, state.T_sat, backend),
        )
    return (
        density_pt(refrigerant, state.T, state.p, backend),
        viscosity_pt(refrigerant, state.T, state.p, backend),
    )


def _on_saturation_line(state):
    return abs(state.T - state.T_sat) <= _SATURATION_FLASH_BAND_K


def _positive(name, value):
    if not math.isfinite(value) or value <= 0.0:
        raise OutOfRangeError(name, value, "> 0", "制冷剂侧几何")
