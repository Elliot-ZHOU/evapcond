"""喷淋水管路的 Darcy 摩擦系数。Colebrook–White 隐式式，Swamee–Jain 只作初值。"""

import math

from evapcond.correlations.registry import record_call
from evapcond.errors import OutOfRangeError
from evapcond.models import CorrelationMeta

COLEBROOK_TOLERANCE = 1e-8
_MAX_ITERATIONS = 50

_CITATION = (
    "C. F. Colebrook. Turbulent flow in pipes, with particular reference to the "
    "transition region between the smooth and rough pipe laws. "
    "Journal of the Institution of Civil Engineers, 1939, 11(4): 133–156. "
    "采用 Darcy λ，不用 Fanning。"
    "初值是 Swamee 与 Jain 1976 年的显式近似 "
    "λ=0.25/[log10(ε/(3.7D)+5.74/Re^0.9)]^2，页码未在本步打开原文核对。"
)
_RANGE = "Re > 0，管径 > 0，绝对粗糙度 >= 0；迭代到 |Δλ| < 1e-8"
_DEVIATION = "拟合实验曲线，无单一百分比偏差"

COLEBROOK_META = CorrelationMeta(
    name="Colebrook–White Darcy λ",
    citation=_CITATION,
    applicability=_RANGE,
    reported_deviation=_DEVIATION,
)


def darcy_friction_factor(reynolds, roughness, diameter):
    """Darcy 摩擦系数 λ。收敛判据是相邻两次迭代的绝对差。"""
    _positive("Re", reynolds)
    _positive("D", diameter)
    if not math.isfinite(roughness) or roughness < 0.0:
        raise OutOfRangeError("epsilon", roughness, ">= 0 m", _CITATION)
    relative = roughness / diameter
    value = _swamee_jain(relative, reynolds)
    for _ in range(_MAX_ITERATIONS):
        updated = _colebrook(relative, reynolds, value)
        if abs(updated - value) < COLEBROOK_TOLERANCE:
            record = record_call(
                COLEBROOK_META,
                (
                    ("Re", reynolds),
                    ("epsilon", roughness),
                    ("D", diameter),
                    ("lambda", updated),
                ),
            )
            return updated, record
        value = updated
    raise OutOfRangeError(
        "lambda",
        value,
        f"Colebrook 迭代 |Δλ| < {COLEBROOK_TOLERANCE}",
        _CITATION,
    )


def _swamee_jain(relative_roughness, reynolds):
    argument = relative_roughness / 3.7 + 5.74 / reynolds**0.9
    if argument <= 0.0:
        raise OutOfRangeError(
            "epsilon/D",
            relative_roughness,
            "使 Swamee–Jain 的对数自变量为正",
            _CITATION,
        )
    return 0.25 / math.log10(argument) ** 2


def _colebrook(relative_roughness, reynolds, factor):
    if factor <= 0.0 or not math.isfinite(factor):
        raise OutOfRangeError("lambda", factor, "> 0", _CITATION)
    argument = relative_roughness / 3.7 + 2.51 / (reynolds * math.sqrt(factor))
    if argument <= 0.0:
        raise OutOfRangeError(
            "epsilon/D",
            relative_roughness,
            "使 Colebrook 的对数自变量为正",
            _CITATION,
        )
    updated = 1.0 / (-2.0 * math.log10(argument)) ** 2
    if not math.isfinite(updated) or updated <= 0.0:
        raise OutOfRangeError("lambda", updated, "> 0 且有限", _CITATION)
    return updated


def _positive(name, value):
    if not math.isfinite(value) or value <= 0.0:
        raise OutOfRangeError(name, value, "> 0", _CITATION)
