"""水平圆管几何。面积与最窄截面风速比只按光管定义。"""

import math
from dataclasses import replace

from evapcond.errors import InputError, OutOfRangeError, UnconfirmedCorrelationError
from evapcond.models import TubeGeometry

UNSUPPORTED_SURFACE_MESSAGE = (
    "板式/低翅片管外侧水膜-空气关联式尚未确认，本期仅支持光管"
)


def require_supported_surface(surface_type):
    """求解入口。只有 tube_plain 可以继续计算。"""
    if surface_type == "tube_plain":
        return
    if surface_type in ("tube_lowfin", "plate"):
        raise UnconfirmedCorrelationError(UNSUPPORTED_SURFACE_MESSAGE)
    raise InputError(
        f"未知表面类型 {surface_type}。有效值：tube_plain、tube_lowfin、plate"
    )


def with_tube_count(tube, n_t):
    """复制管束并写入并联回路数 N_t。"""
    if type(n_t) is not int or n_t < 1:
        raise InputError("N_t 必须是正整数")
    return replace(tube, N_t=n_t)


def face_area(tube):
    """迎风面积 A_f = N_t · S_T · L，m²。"""
    _require_tube(tube)
    return tube.N_t * tube.S_T * tube.L


def outside_area(tube):
    """总管外表面积 N_t · N_r · π · d_o · L，m²。"""
    require_supported_surface(tube.surface_type)
    return tube.N_t * tube.N_r * segment_outside_area(tube, tube.L)


def inside_area(tube):
    """总管内表面积 N_t · N_r · π · d_i · L，m²。"""
    require_supported_surface(tube.surface_type)
    return tube.N_t * tube.N_r * math.pi * tube.d_i * tube.L


def segment_outside_area(tube, length):
    """单根管、长度为 length 的外表面积 π · d_o · length，m²。"""
    require_supported_surface(tube.surface_type)
    _require_tube(tube)
    if not math.isfinite(length) or length <= 0.0:
        raise OutOfRangeError("dL", length, "> 0 m", "管段长度")
    return math.pi * tube.d_o * length


def velocity_max_over_face(tube):
    """叉排最窄截面风速与迎面风速之比。

    斜向节距 S_D = sqrt(S_L² + (S_T/2)²)。
    当 S_D < (S_T + d_o)/2 时，最窄截面在斜向，
    比值为 S_T / (2 (S_D - d_o))；否则在横向，比值为 S_T / (S_T - d_o)。
    """
    require_supported_surface(tube.surface_type)
    _require_tube(tube)
    diagonal = math.sqrt(tube.S_L**2 + (tube.S_T / 2.0) ** 2)
    if diagonal < (tube.S_T + tube.d_o) / 2.0:
        opening = 2.0 * (diagonal - tube.d_o)
    else:
        opening = tube.S_T - tube.d_o
    if opening <= 0.0:
        raise OutOfRangeError(
            "S_T",
            tube.S_T,
            "最窄流道宽度为正",
            "叉排管束几何",
        )
    return tube.S_T / opening


def _require_tube(tube):
    if not isinstance(tube, TubeGeometry):
        raise InputError("需要 TubeGeometry")
