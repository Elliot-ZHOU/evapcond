"""空气侧显热、蒸发和潜热。空气温度只由焓和含湿量反算。"""

import math
from dataclasses import dataclass

from evapcond.correlations.film_air import (
    air_convection_coefficient,
    bosnjakovic_lewis_factor,
    film_convection_coefficient,
)
from evapcond.errors import InputError, OutOfRangeError
from evapcond.geometry.tube import face_area, require_supported_surface
from evapcond.models import TubeGeometry
from evapcond.properties.humid_air import humid_air_state
from evapcond.properties.water import latent_heat, vapor_enthalpy


@dataclass(frozen=True)
class AirSideFlux:
    """一个控制容积的空气侧结果。焓为 J/kg 干空气，流量为 kg 干空气/s。"""

    dQ_s: float
    dm_ev: float
    dQ_l: float
    h_c: float
    h_w: float
    h_m: float
    le_f: float
    R_film: float
    outlet: object
    correlations: tuple


def gamma_m_from_spray(m_spray, d_o, area_face):
    """Γ_m = m_spray · d_o / (2 A_f)，kg/(m·s)。"""
    _positive_flow("m_spray", m_spray)
    _positive_flow("d_o", d_o)
    _positive_flow("A_f", area_face)
    return m_spray * d_o / (2.0 * area_face)


def gamma_m_from_gamma(gamma, d_o, s_t):
    """由单侧线密度得到 Γ_m = Γ · d_o / S_T。"""
    _positive_flow("Gamma", gamma)
    _positive_flow("d_o", d_o)
    _positive_flow("S_T", s_t)
    return gamma * d_o / s_t


def spray_mass_flow(gamma, n_t, length):
    """喷淋水量 = Γ · 2 · N_t · L，kg/s。"""
    _positive_flow("Gamma", gamma)
    if type(n_t) is not int or n_t < 1:
        raise InputError("N_t 必须是正整数")
    _positive_flow("L", length)
    return gamma * 2.0 * n_t * length


def dry_air_mass_flow(state, v_face, area_face):
    """迎面风速对应的干空气质量流量，kg/s。"""
    if not math.isfinite(v_face) or v_face <= 0.0:
        raise InputError("v_f 必须大于 0")
    _positive_flow("A_f", area_face)
    return state.rho * v_face * area_face / (1.0 + state.w)


def film_resistance(h_w, area):
    """R_film = 1 / (h_w A_o)，K/W。不并入 h_c。"""
    _positive_flow("h_w", h_w)
    _positive_flow("A_o", area)
    return 1.0 / (h_w * area)


def saturation_humidity(T_film, pressure):
    """水膜温度下的饱和含湿量，kg/kg。"""
    return humid_air_state(pressure, T_db=T_film, rh=1.0).w


def air_side_rates(h_c, h_m, area, T_film, T_air, w_s, w_air, h_fg):
    """显热、蒸发量和潜热分开计算。"""
    dQ_s = h_c * area * (T_film - T_air)
    dm_ev = h_m * area * (w_s - w_air)
    dQ_l = dm_ev * h_fg
    return dQ_s, dm_ev, dQ_l


def advance_moist_air(inlet, m_dry, dQ_s, dm_ev, i_g):
    """用 ṁ_a di = dQ_s + dm_ev·i_g 更新空气，再由 (i, w, p) 求温度。"""
    _positive_flow("m_dry", m_dry)
    w_out = inlet.w + dm_ev / m_dry
    enthalpy_out = inlet.h + (dQ_s + dm_ev * i_g) / m_dry
    return humid_air_state(inlet.p, w=w_out, h=enthalpy_out)


def evaluate_air_side(tube, inlet, T_film, area, m_dry, gamma=None, m_spray=None, le_f=None):
    """计算一个光管控制容积。喷淋密度 Γ 与喷淋水量只能给一个。"""
    if not isinstance(tube, TubeGeometry):
        raise InputError("需要 TubeGeometry")
    require_supported_surface(tube.surface_type)
    if (gamma is None) == (m_spray is None):
        raise InputError("喷淋水量与 Γ 必须二选一")
    if gamma is None:
        gamma_m = gamma_m_from_spray(m_spray, tube.d_o, face_area(tube))
    else:
        gamma_m = gamma_m_from_gamma(gamma, tube.d_o, tube.S_T)
    h_c, hc_record = air_convection_coefficient(gamma_m, tube.d_o)
    h_w, hw_record = film_convection_coefficient(gamma_m, tube.d_o)
    w_s = saturation_humidity(T_film, inlet.p)
    lewis, lewis_record = bosnjakovic_lewis_factor(w_s, inlet.w, le_f=le_f)
    h_m = h_c / (inlet.cp * lewis)
    h_fg = latent_heat(T_film)
    i_g = vapor_enthalpy(T_film)
    dQ_s, dm_ev, dQ_l = air_side_rates(
        h_c, h_m, area, T_film, inlet.T_db, w_s, inlet.w, h_fg
    )
    outlet = advance_moist_air(inlet, m_dry, dQ_s, dm_ev, i_g)
    return AirSideFlux(
        dQ_s=dQ_s,
        dm_ev=dm_ev,
        dQ_l=dQ_l,
        h_c=h_c,
        h_w=h_w,
        h_m=h_m,
        le_f=lewis,
        R_film=film_resistance(h_w, area),
        outlet=outlet,
        correlations=(hc_record, hw_record, lewis_record),
    )


def _positive_flow(name, value):
    if not math.isfinite(value) or value <= 0.0:
        raise OutOfRangeError(name, value, "> 0", "空气侧流量或面积")
