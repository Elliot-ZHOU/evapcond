"""管内单相对流。Gnielinski (1976) 的公开转写，只用于过热段和过冷段。"""

import math

from evapcond.correlations.registry import record_call
from evapcond.errors import OutOfRangeError
from evapcond.models import CorrelationMeta

GNIELINSKI_RE_MIN = 2300.0
GNIELINSKI_RE_TRANSITION = 3000.0
GNIELINSKI_RE_MAX = 5.0e6
GNIELINSKI_PR_MIN = 0.5
GNIELINSKI_PR_MAX = 2000.0

GNIELINSKI_TRANSITION_WARNING = (
    "Gnielinski (1976) 关联式在 2300 ≤ Re < 3000 时仍按该式计算，"
    "该区间低于公开转写常用下限 3000"
)

_CITATION = (
    "V. Gnielinski. New equations for heat and mass transfer in turbulent pipe "
    "and channel flow. International Chemical Engineering, 1976, 16(2): 359–368. "
    "系数与范围按 2026-11-03 补充二确认的公开转写。"
)
_RANGE = "0.5 ≤ Pr ≤ 2000；2300 ≤ Re ≤ 5×10^6。Re < 2300 与 Re > 5×10^6 越界"
_DEVIATION = "补充二未给出百分比偏差"

GNIELINSKI_META = CorrelationMeta(
    name="Gnielinski (1976)",
    citation=_CITATION,
    applicability=_RANGE,
    reported_deviation=_DEVIATION,
)


def gnielinski_coefficient(G, D, mu, Pr, k):
    """单相对流系数，W/(m²·K)。Re < 2300 时抛出 OutOfRangeError。"""
    _positive("G", G)
    _positive("D", D)
    _positive("mu", mu)
    _positive("k", k)
    re = G * D / mu
    nu, warnings = gnielinski_nusselt(re, Pr)
    h = nu * k / D
    if not math.isfinite(h) or h <= 0.0:
        raise OutOfRangeError("h", h, "> 0", _CITATION)
    record = record_call(
        GNIELINSKI_META,
        (("G", G), ("D", D), ("Re", re), ("Pr", Pr), ("Nu", nu)),
    )
    return h, record, warnings


def gnielinski_nusselt(Re, Pr):
    """努塞尔数。2300 ≤ Re < 3000 时计算并写警告。"""
    if not math.isfinite(Re) or Re < GNIELINSKI_RE_MIN or Re > GNIELINSKI_RE_MAX:
        raise OutOfRangeError("Re", Re, "[2300, 5e6]", _CITATION)
    if not math.isfinite(Pr) or Pr < GNIELINSKI_PR_MIN or Pr > GNIELINSKI_PR_MAX:
        raise OutOfRangeError("Pr", Pr, "[0.5, 2000]", _CITATION)
    f = (0.790 * math.log(Re) - 1.64) ** -2
    numerator = (f / 8.0) * (Re - 1000.0) * Pr
    denominator = 1.0 + 12.7 * math.sqrt(f / 8.0) * (Pr ** (2.0 / 3.0) - 1.0)
    if denominator <= 0.0:
        raise OutOfRangeError("Pr", Pr, "使 Gnielinski 分母为正", _CITATION)
    nu = numerator / denominator
    if not math.isfinite(nu) or nu <= 0.0:
        raise OutOfRangeError("Nu", nu, "> 0", _CITATION)
    warnings = ()
    if Re < GNIELINSKI_RE_TRANSITION:
        warnings = (GNIELINSKI_TRANSITION_WARNING,)
    return nu, warnings


def _positive(name, value):
    if not math.isfinite(value) or value <= 0.0:
        raise OutOfRangeError(name, value, "> 0", _CITATION)
