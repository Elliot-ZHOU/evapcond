"""两相摩擦压降与均相加速压降。

摩擦系数是 Blasius / 层流 Fanning 形式，不是 Friedel 原文的摩擦系数。
E、F、H、Fr、We 采用 docs/PLAN.md 中已定稿的公开转写。
加速压降用均相比容 v = x/ρ_g + (1-x)/ρ_l，Δp_acc = G² (v_out - v_in)。
"""

import math

from evapcond.correlations.registry import record_call
from evapcond.errors import OutOfRangeError
from evapcond.models import CorrelationMeta

# 标准重力加速度。第 3 届国际计量大会（1901）规定值，m/s²。
STANDARD_GRAVITY = 9.80665

_FRIEDEL_CITATION = (
    "L. Friedel. Improved friction pressure drop correlations for horizontal and "
    "vertical two-phase pipe flow. European Two-Phase Flow Group Meeting, Ispra, "
    "1979, Paper E2. E、F、H、Fr、We 用 docs/PLAN.md 的公开转写；"
    "单相摩擦系数用 Blasius，不是 Friedel 原文摩擦系数。"
)
_FRIEDEL_RANGE = "0 ≤ x ≤ 1；G、D、密度、粘度、表面张力均为正；μ_g < μ_l"
_FRIEDEL_DEVIATION = "二次文献称水平单组分相对标准差约 32%，本轮未对原文表核对"

FRIEDEL_META = CorrelationMeta(
    name="Friedel (1979) 乘子 + Blasius",
    citation=_FRIEDEL_CITATION,
    applicability=_FRIEDEL_RANGE,
    reported_deviation=_FRIEDEL_DEVIATION,
)

_ACCEL_META = CorrelationMeta(
    name="均相加速压降",
    citation=(
        "docs/PLAN.md 定稿：v = x/ρ_g + (1-x)/ρ_l，"
        "Δp_acc = G² (v_out - v_in)。空泡份额模型补充二未另指定。"
    ),
    applicability="控制容积两端的比容由当地干度或单相密度给出",
    reported_deviation="未给出",
)


def fanning_friction_factor(Re):
    """Fanning 摩擦系数。Re < 2300 用 16/Re，否则用 0.079 Re^{-0.25}。"""
    if not math.isfinite(Re) or Re <= 0.0:
        raise OutOfRangeError("Re", Re, "> 0", _FRIEDEL_CITATION)
    if Re < 2300.0:
        return 16.0 / Re
    return 0.079 * Re**-0.25


def friedel_friction_gradient(G, D, x, rho_l, rho_g, mu_l, mu_g, sigma):
    """两相摩擦压降梯度，Pa/m。干度 0 与 1 退化为对应的单相梯度。"""
    _positive("G", G)
    _positive("D", D)
    _positive("rho_l", rho_l)
    _positive("rho_g", rho_g)
    _positive("mu_l", mu_l)
    _positive("mu_g", mu_g)
    _positive("sigma", sigma)
    if not math.isfinite(x) or x < 0.0 or x > 1.0:
        raise OutOfRangeError("x", x, "[0, 1]", _FRIEDEL_CITATION)
    if mu_g >= mu_l:
        raise OutOfRangeError("mu_g/mu_l", mu_g / mu_l, "< 1", _FRIEDEL_CITATION)
    re_lo = G * D / mu_l
    re_go = G * D / mu_g
    f_lo = fanning_friction_factor(re_lo)
    f_go = fanning_friction_factor(re_go)
    e_factor = (1.0 - x) ** 2 + x**2 * (rho_l * f_go) / (rho_g * f_lo)
    if x == 0.0 or x == 1.0:
        phi2 = e_factor
    else:
        f_factor = x**0.78 * (1.0 - x) ** 0.224
        h_factor = (
            (rho_l / rho_g) ** 0.91
            * (mu_g / mu_l) ** 0.19
            * (1.0 - mu_g / mu_l) ** 0.7
        )
        rho_h = 1.0 / (x / rho_g + (1.0 - x) / rho_l)
        fr = G**2 / (STANDARD_GRAVITY * D * rho_h**2)
        we = G**2 * D / (sigma * rho_h)
        phi2 = e_factor + 3.24 * f_factor * h_factor / (fr**0.045 * we**0.035)
    if not math.isfinite(phi2) or phi2 <= 0.0:
        raise OutOfRangeError("Phi_lo^2", phi2, "> 0 且有限", _FRIEDEL_CITATION)
    gradient = phi2 * 2.0 * f_lo * G**2 / (D * rho_l)
    if not math.isfinite(gradient) or gradient < 0.0:
        raise OutOfRangeError("dp/dz", gradient, "≥ 0 且有限", _FRIEDEL_CITATION)
    record = record_call(
        FRIEDEL_META,
        (
            ("G", G),
            ("D", D),
            ("x", x),
            ("Re_lo", re_lo),
            ("Re_go", re_go),
            ("Phi_lo^2", phi2),
        ),
    )
    return gradient, record


def single_phase_friction_gradient(G, D, rho, mu):
    """单相摩擦压降梯度，Pa/m。摩擦系数与 Friedel 中的 f_lo、f_go 相同。"""
    _positive("G", G)
    _positive("D", D)
    _positive("rho", rho)
    _positive("mu", mu)
    re = G * D / mu
    f = fanning_friction_factor(re)
    gradient = 2.0 * f * G**2 / (D * rho)
    if not math.isfinite(gradient) or gradient < 0.0:
        raise OutOfRangeError("dp/dz", gradient, "≥ 0 且有限", _FRIEDEL_CITATION)
    record = record_call(
        FRIEDEL_META,
        (("G", G), ("D", D), ("Re", re), ("f", f)),
    )
    return gradient, record


def homogeneous_specific_volume(x, rho_l, rho_g):
    """均相比容，m³/kg。"""
    _positive("rho_l", rho_l)
    _positive("rho_g", rho_g)
    if not math.isfinite(x) or x < 0.0 or x > 1.0:
        raise OutOfRangeError("x", x, "[0, 1]", _ACCEL_META.citation)
    return x / rho_g + (1.0 - x) / rho_l


def acceleration_pressure_drop(G, v_in, v_out):
    """均相加速压降，Pa。冷凝时出口比容更小，此项为负。"""
    _positive("G", G)
    _positive("v_in", v_in)
    _positive("v_out", v_out)
    drop = G**2 * (v_out - v_in)
    if not math.isfinite(drop):
        raise OutOfRangeError("dp_acc", drop, "有限值", _ACCEL_META.citation)
    record = record_call(
        _ACCEL_META,
        (("G", G), ("v_in", v_in), ("v_out", v_out), ("dp_acc", drop)),
    )
    return drop, record


def _positive(name, value):
    if not math.isfinite(value) or value <= 0.0:
        raise OutOfRangeError(name, value, "> 0", _FRIEDEL_CITATION)
