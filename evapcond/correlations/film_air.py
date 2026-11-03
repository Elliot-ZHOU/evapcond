"""管外水膜与空气的 Mizushina 关联式，以及 Bosnjaković 刘易斯因子。"""

import math

from evapcond.correlations.registry import record_call
from evapcond.errors import OutOfRangeError
from evapcond.models import CorrelationMeta

MIZUSHINA_COEFFICIENT = 2102.9
MIZUSHINA_RATIO_MIN = 0.195
MIZUSHINA_RATIO_MAX = 5.556
MIZUSHINA_DIAMETERS_MM = (12.7, 19.05, 40.0)
LEWIS_LIMIT = 0.865 ** (2.0 / 3.0)

MIZUSHINA_NOTE = (
    "管外空气对流项采用 Mizushina et al. (1967) 关联式，经 Γ 定义转换后使用；"
    "该式对纯空气对流与空气-水膜耦合对流的区分未在原文中显式声明，"
    "其量纲与数值范围与蒸发式冷凝器管外工况一致。"
)

_MIZUSHINA_CITATION = (
    "T. Mizushina, R. Ito, H. Miyashita. Experimental study of evaporative cooler. "
    "化学工学, 1967, 31(5): 469–473. DOI: 10.1252/kakoronbunshu1953.31.469. "
    "系数、指数与范围按 2026-11-03 补充二确认。"
)
_MIZUSHINA_RANGE = (
    "d_o 仅为 12.7、19.05、40 mm；0.195 < Gamma_m/d_o < 5.556 kg/(m^2·s)"
)
_MIZUSHINA_DEVIATION = "原文未给出百分比偏差"

HC_META = CorrelationMeta(
    name="Mizushina h_c",
    citation=_MIZUSHINA_CITATION,
    applicability=_MIZUSHINA_RANGE,
    reported_deviation=_MIZUSHINA_DEVIATION,
)
HW_META = CorrelationMeta(
    name="Mizushina h_w",
    citation=_MIZUSHINA_CITATION,
    applicability=_MIZUSHINA_RANGE,
    reported_deviation=_MIZUSHINA_DEVIATION,
)
LEWIS_META = CorrelationMeta(
    name="Bosnjakovic Le_f",
    citation=(
        "用户确认的 Bosnjaković 刘易斯因子，公式见 docs/correlations.md "
        "「用户确认」第 2 节（2026-11-03，补充二）。未另附页码。"
    ),
    applicability="空气–水；w_s 与 w_a 为非负含湿量。w_s→w_a 时取 0.865^(2/3)。可覆盖为 Le_f=1。",
    reported_deviation="补充二未给出百分比偏差",
)


def air_convection_coefficient(gamma_m, d_o):
    """管外空气对流 h_c，W/(m²·K)。与水膜系数分开调用。"""
    value = _mizushina(gamma_m, d_o)
    return value, record_call(
        HC_META,
        (("Gamma_m", gamma_m), ("d_o", d_o), ("Gamma_m/d_o", gamma_m / d_o)),
    )


def film_convection_coefficient(gamma_m, d_o):
    """水膜对流 h_w，W/(m²·K)。公式与 h_c 相同，热阻单独串联。"""
    value = _mizushina(gamma_m, d_o)
    return value, record_call(
        HW_META,
        (("Gamma_m", gamma_m), ("d_o", d_o), ("Gamma_m/d_o", gamma_m / d_o)),
    )


def bosnjakovic_lewis_factor(w_s, w_a, le_f=None):
    """默认 Bosnjaković 因子。传入 le_f 时使用该正值，不再乘 2/3。"""
    if le_f is not None:
        if not math.isfinite(le_f) or le_f <= 0.0:
            raise OutOfRangeError("Le_f", le_f, "> 0", "刘易斯因子覆盖值")
        value = float(le_f)
    else:
        value = _bosnjakovic(w_s, w_a)
    return value, record_call(
        LEWIS_META,
        (("w_s", w_s), ("w_a", w_a), ("Le_f", value)),
    )


def _mizushina(gamma_m, d_o):
    if not math.isfinite(d_o) or d_o <= 0.0:
        raise OutOfRangeError("d_o", d_o, "12.7、19.05 或 40 mm", _MIZUSHINA_CITATION)
    diameter_mm = d_o * 1000.0
    if not any(abs(diameter_mm - item) <= 1e-4 for item in MIZUSHINA_DIAMETERS_MM):
        raise OutOfRangeError(
            "d_o",
            d_o,
            "12.7、19.05 或 40 mm",
            _MIZUSHINA_CITATION,
        )
    if not math.isfinite(gamma_m):
        raise OutOfRangeError(
            "Gamma_m/d_o",
            gamma_m,
            "0.195 < Gamma_m/d_o < 5.556 kg/(m^2·s)",
            _MIZUSHINA_CITATION,
        )
    ratio = gamma_m / d_o
    if ratio <= MIZUSHINA_RATIO_MIN or ratio >= MIZUSHINA_RATIO_MAX:
        raise OutOfRangeError(
            "Gamma_m/d_o",
            ratio,
            "0.195 < Gamma_m/d_o < 5.556 kg/(m^2·s)",
            _MIZUSHINA_CITATION,
        )
    return MIZUSHINA_COEFFICIENT * ratio ** (1.0 / 3.0)


def _bosnjakovic(w_s, w_a):
    for name, value in (("w_s", w_s), ("w_a", w_a)):
        if not math.isfinite(value) or value < 0.0:
            raise OutOfRangeError(name, value, ">= 0 kg/kg", LEWIS_META.citation)
    ratio = (w_s + 0.622) / (w_a + 0.622)
    if abs(ratio - 1.0) < 1e-8:
        return LEWIS_LIMIT
    return LEWIS_LIMIT * (ratio - 1.0) / math.log(ratio)
