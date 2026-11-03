"""管内冷凝。按补充二写出的 Shah 公式，文献标签为 Shah (2009)。"""

import math

from evapcond.correlations.registry import record_call
from evapcond.errors import OutOfRangeError
from evapcond.models import CorrelationMeta

SHAH_RE_LO_MIN = 100.0
SHAH_RE_LO_MAX = 63000.0
SHAH_PR_MIN = 1.0
SHAH_PR_MAX = 13.0
SHAH_RE_GT_CAUTION = 35000.0

SHAH_LOW_RE_GT_WARNING = (
    "Shah (2009) 关联式在 Re_GT ≤ 35000 时原文建议保守使用，当前设计工况低于该阈值"
)

_CITATION = (
    "M. M. Shah. An improved and extended general correlation for heat transfer "
    "during condensation in plain tubes. HVAC&R Research, 2009, 15(5): 889–913. "
    "实现采用 2026-11-03 补充二写出的公式，与 Shah (1979) 公开形式相同；"
    "不含 2009 年粘度比修正。"
)
_RANGE = "液相雷诺数 Re_lo = G D/μ_l 为 100–63000；液相普朗特数 1–13；0 ≤ x < 1"
_DEVIATION = "补充二声明平均偏差 15–17%。该数字与 2009 年论文摘要的 14.4% 不一致"

SHAH_META = CorrelationMeta(
    name="Shah (2009) 补充二写出式",
    citation=_CITATION,
    applicability=_RANGE,
    reported_deviation=_DEVIATION,
)


def shah_condensation_coefficient(G, D, x, p, p_crit, mu_l, Pr_l, k_l):
    """两相冷凝系数 h_TP，W/(m²·K)。

    Re_GT 取全液相雷诺数 G D/μ_l。Re_GT ≤ 35000 时仍返回数值，并给出警告。
    """
    _positive("G", G)
    _positive("D", D)
    _positive("p", p)
    _positive("p_crit", p_crit)
    _positive("mu_l", mu_l)
    _positive("k_l", k_l)
    if not math.isfinite(x) or x < 0.0 or x >= 1.0:
        raise OutOfRangeError("x", x, "0 ≤ x < 1", _CITATION)
    if not math.isfinite(Pr_l) or Pr_l < SHAH_PR_MIN or Pr_l > SHAH_PR_MAX:
        raise OutOfRangeError("Pr_l", Pr_l, "[1, 13]", _CITATION)
    re_lo = G * D / mu_l
    if re_lo < SHAH_RE_LO_MIN or re_lo > SHAH_RE_LO_MAX:
        raise OutOfRangeError("Re_lo", re_lo, "[100, 63000]", _CITATION)
    p_r = p / p_crit
    if p_r <= 0.0 or p_r >= 1.0:
        raise OutOfRangeError("p_r", p_r, "(0, 1)", _CITATION)
    h_lo = 0.023 * re_lo**0.8 * Pr_l**0.4 * k_l / D
    bracket = (1.0 - x) ** 0.8 + 3.8 * x**0.76 * (1.0 - x) ** 0.04 / p_r**0.38
    h_tp = h_lo * bracket
    if not math.isfinite(h_tp) or h_tp <= 0.0:
        raise OutOfRangeError("h_TP", h_tp, "> 0", _CITATION)
    warnings = ()
    if re_lo <= SHAH_RE_GT_CAUTION:
        warnings = (SHAH_LOW_RE_GT_WARNING,)
    record = record_call(
        SHAH_META,
        (
            ("G", G),
            ("D", D),
            ("x", x),
            ("Re_lo", re_lo),
            ("Re_GT", re_lo),
            ("Pr_l", Pr_l),
            ("p_r", p_r),
        ),
    )
    return h_tp, record, warnings


def _positive(name, value):
    if not math.isfinite(value) or value <= 0.0:
        raise OutOfRangeError(name, value, "> 0", _CITATION)
