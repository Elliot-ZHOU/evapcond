"""错列光管管束压降。系数按补充四，并与 zukauskas_euler_table.png 一致。

欧拉数是图上的逆幂级数，k_1 本期取 1。管排修正 C_2 乘在压降上，不写进级数。
相邻雷诺数区间的公共端点归入较高雷诺数那一行；各间距比的最低下界和最高上界仍包含在内。
级数在表内个别雷诺数上会非正，此时抛出 OutOfRangeError，不把压降截成正数。
"""

import math

from evapcond.correlations.registry import record_call
from evapcond.errors import InputError, OutOfRangeError
from evapcond.models import CorrelationMeta

# (a, Re_min, Re_max, 上界是否包含, q, r, s, t, u)
EULER_ROWS = (
    (1.25, 3.0, 1.0e3, False, 0.795, 0.247e3, 0.335e3, -0.155e4, 0.241e4),
    (1.25, 1.0e3, 2.0e6, True, 0.245, 0.339e4, -0.984e7, 0.132e11, -0.599e13),
    (1.5, 3.0, 1.0e3, False, 0.683, 0.111e3, -0.973e2, 0.426e3, -0.574e3),
    (1.5, 1.0e3, 2.0e6, True, 0.203, 0.248e4, -0.758e7, 0.104e11, -0.482e13),
    (2.0, 7.0, 1.0e2, False, 0.713, 0.448e2, -0.126e3, -0.582e3, 0.0),
    (2.0, 1.0e2, 1.0e4, False, 0.343, 0.303e3, -0.717e5, 0.880e7, -0.380e9),
    (2.0, 1.0e4, 2.0e6, True, 0.162, 0.181e4, -0.792e8, -0.165e13, 0.872e16),
    (2.5, 1.0e2, 5.0e3, False, 0.330, 0.989e2, -0.148e5, 0.192e7, 0.862e8),
    (2.5, 5.0e3, 2.0e6, True, 0.119, 0.848e4, -0.507e8, 0.251e12, -0.463e15),
)

# 本期不查 k_1 表。非等边布置也乘 1，并在结果里说明。
K1 = 1.0
GAMMA_REF = 2.8755
WET_COEFFICIENT = 0.5

ZUKAUSKAS_BASIS_NOTE = (
    "干管束压降基于 Zukauskas 错列管束关联式，湿工况在此基础乘上由 Γ 驱动的湿修正因子。"
)
EQUILATERAL_K1_NOTE = (
    "当前干管束压降按等边错列计算，非等边几何需补充 Zukauskas 的 k_1 修正表。"
)
WET_ESTIMATE_NOTE = "湿工况压降为工程估计，不确定度约 ±30%"

_A_VALUES = (1.25, 1.5, 2.0, 2.5)
_A_TOLERANCE = 1e-8

_EULER_CITATION = (
    "A. Žukauskas, R. Ulinskas. Banks of plain and finned tubes. "
    "Heat Exchanger Design Handbook. 补充四把年份写作 1983。"
    "系数按 docs/sources/zukauskas_euler_table.png，与 docs/correlations.md 补充四表一致。"
    "k_1 本期取 1。"
)
_EULER_RANGE = "a = S_T/d_o 仅为 1.25、1.5、2.0、2.5，且 Re_max 落在该行的雷诺数区间内"
_EULER_DEVIATION = "补充四未给出百分比偏差"

EULER_META = CorrelationMeta(
    name="Zukauskas–Ulinskas 错列光管欧拉数",
    citation=_EULER_CITATION,
    applicability=_EULER_RANGE,
    reported_deviation=_EULER_DEVIATION,
)
ROW_CORRECTION_META = CorrelationMeta(
    name="管排修正 C_2",
    citation=(
        "2026-11-03 补充四给出的拟合式，不是从 Zukauskas 原图逐点读出的表。"
        "N_r<10 时 C_2=1-0.45 exp(-N_r/3)，否则 C_2=1。"
    ),
    applicability="N_r 为正整数",
    reported_deviation="拟合式，补充四未给出百分比偏差",
)
WET_META = CorrelationMeta(
    name="湿工况管束压降修正",
    citation=(
        "2026-11-03 补充二给出系数 0.5；"
        "Γ_ref=2.8755 kg/(m^2·s) 由补充三按 Mizushina 有效范围中值批准。"
        "这不是实验回归。"
    ),
    applicability="Δp_wet = Δp_dry (1 + 0.5 (Γ_m/d_o) / Γ_ref)，Γ_ref=2.8755 kg/(m^2·s)",
    reported_deviation=WET_ESTIMATE_NOTE,
)


def euler_number(spacing_ratio, reynolds):
    """图上的欧拉数，已乘 k_1=1。雷诺数用最窄截面风速。"""
    nominal = _nominal_spacing(spacing_ratio)
    row = _select_row(nominal, reynolds)
    q, r, s, t, u = row[4:]
    eu = K1 * _polynomial(q, r, s, t, u, reynolds)
    if not math.isfinite(eu) or eu <= 0.0:
        raise OutOfRangeError(
            "Eu",
            eu,
            "> 0",
            _EULER_CITATION + " 逆幂级数在该雷诺数上非正，不截断、不外推。",
        )
    record = record_call(
        EULER_META,
        (
            ("a", nominal),
            ("Re_max", reynolds),
            ("q", q),
            ("r", r),
            ("s", s),
            ("t", t),
            ("u", u),
            ("k_1", K1),
            ("Eu", eu),
        ),
    )
    return eu, record


def row_correction(n_r):
    """管排数修正 C_2。"""
    if type(n_r) is not int or n_r < 1:
        raise InputError("N_r 必须是正整数")
    if n_r < 10:
        value = 1.0 - 0.45 * math.exp(-n_r / 3.0)
    else:
        value = 1.0
    record = record_call(
        ROW_CORRECTION_META,
        (("N_r", n_r), ("C_2", value)),
    )
    return value, record


def dry_bundle_pressure_drop(rho, v_max, n_r, euler, c2):
    """Δp_dry = C_2 · Eu · ½ ρ V_max² · N_r，Pa。"""
    _positive("rho", rho, _EULER_CITATION)
    _positive("V_max", v_max, _EULER_CITATION)
    _positive("Eu", euler, _EULER_CITATION)
    _positive("C_2", c2, ROW_CORRECTION_META.citation)
    if type(n_r) is not int or n_r < 1:
        raise InputError("N_r 必须是正整数")
    drop = c2 * euler * 0.5 * rho * v_max**2 * n_r
    if not math.isfinite(drop) or drop <= 0.0:
        raise OutOfRangeError("dp_dry", drop, "> 0 Pa", _EULER_CITATION)
    return drop


def wet_pressure_drop(dp_dry, gamma_m, d_o):
    """湿修正后的管束压降，Pa。"""
    _positive("dp_dry", dp_dry, WET_META.citation)
    _positive("Gamma_m", gamma_m, WET_META.citation)
    _positive("d_o", d_o, WET_META.citation)
    ratio = gamma_m / d_o
    factor = 1.0 + WET_COEFFICIENT * ratio / GAMMA_REF
    drop = dp_dry * factor
    if not math.isfinite(drop) or drop <= 0.0:
        raise OutOfRangeError("dp_wet", drop, "> 0 Pa", WET_META.citation)
    record = record_call(
        WET_META,
        (
            ("Gamma_m", gamma_m),
            ("d_o", d_o),
            ("Gamma_m/d_o", ratio),
            ("Gamma_ref", GAMMA_REF),
            ("factor", factor),
            ("dp_wet", drop),
        ),
    )
    return drop, record


def _nominal_spacing(spacing_ratio):
    if not math.isfinite(spacing_ratio):
        raise OutOfRangeError(
            "S_T/d_o",
            spacing_ratio,
            "1.25、1.5、2.0 或 2.5",
            _EULER_CITATION,
        )
    for nominal in _A_VALUES:
        if abs(spacing_ratio - nominal) <= _A_TOLERANCE:
            return nominal
    raise OutOfRangeError(
        "S_T/d_o",
        spacing_ratio,
        "1.25、1.5、2.0 或 2.5",
        _EULER_CITATION,
    )


def _select_row(nominal, reynolds):
    if not math.isfinite(reynolds) or reynolds <= 0.0:
        raise OutOfRangeError("Re_max", reynolds, "> 0", _EULER_CITATION)
    for row in EULER_ROWS:
        if row[0] != nominal:
            continue
        lower, upper, upper_inclusive = row[1], row[2], row[3]
        if reynolds < lower:
            continue
        if upper_inclusive and reynolds <= upper:
            return row
        if not upper_inclusive and reynolds < upper:
            return row
    raise OutOfRangeError(
        "Re_max",
        reynolds,
        _range_text(nominal),
        _EULER_CITATION,
    )


def _range_text(nominal):
    parts = []
    for row in EULER_ROWS:
        if row[0] != nominal:
            continue
        lower, upper, upper_inclusive = row[1], row[2], row[3]
        right = "<=" if upper_inclusive else "<"
        parts.append(f"{lower:g} <= Re {right} {upper:g}")
    return " 或 ".join(parts)


def _polynomial(q, r, s, t, u, reynolds):
    inverse = 1.0 / reynolds
    return q + inverse * (r + inverse * (s + inverse * (t + inverse * u)))


def _positive(name, value, source):
    if not math.isfinite(value) or value <= 0.0:
        raise OutOfRangeError(name, value, "> 0", source)
