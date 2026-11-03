"""跨模块传递的数据结构。后续步骤只在本文件追加 dataclass。"""

import math
from dataclasses import dataclass

from evapcond.errors import InputError, OutOfRangeError


@dataclass(frozen=True)
class TubeGeometry:
    """水平圆管管束。长度单位为 m，导热系数为 W/(m·K)。

    低翅片管保留翅高、翅距、翅厚。本期求解只接受 surface_type=tube_plain。
    """

    surface_type: str
    d_o: float
    wall_thickness: float
    k_w: float
    S_T: float
    S_L: float
    N_r: int
    N_t: int
    L: float
    fin_height: float | None = None
    fin_pitch: float | None = None
    fin_thickness: float | None = None
    arrangement: str = "staggered"

    def __post_init__(self):
        if self.surface_type not in ("tube_plain", "tube_lowfin"):
            raise InputError(
                f"未知表面类型 {self.surface_type}。管几何只接受 tube_plain 或 tube_lowfin"
            )
        if self.arrangement != "staggered":
            raise InputError("本期管排布置只有叉排 staggered")
        _positive("d_o", self.d_o)
        _positive("wall_thickness", self.wall_thickness)
        _positive("k_w", self.k_w)
        _positive("S_L", self.S_L)
        _positive("L", self.L)
        _positive_int("N_r", self.N_r)
        _positive_int("N_t", self.N_t)
        if self.d_i <= 0.0:
            raise OutOfRangeError(
                "wall_thickness",
                self.wall_thickness,
                f"< {self.d_o / 2.0} m",
                "d_i = d_o - 2δ 必须为正",
            )
        if self.S_T <= self.d_o:
            raise OutOfRangeError(
                "S_T",
                self.S_T,
                f"> {self.d_o} m",
                "横向管距必须大于外径",
            )
        diagonal = math.sqrt(self.S_L**2 + (self.S_T / 2.0) ** 2)
        if diagonal <= self.d_o:
            raise OutOfRangeError(
                "S_L",
                self.S_L,
                "叉排斜向间距大于外径",
                "管子在斜向上不得重叠",
            )
        fins = (self.fin_height, self.fin_pitch, self.fin_thickness)
        if self.surface_type == "tube_plain":
            if any(item is not None for item in fins):
                raise InputError("光管不填写翅高、翅距、翅厚")
        else:
            if any(item is None for item in fins):
                raise InputError("低翅片管必须同时给出翅高、翅距、翅厚")
            _positive("fin_height", self.fin_height)
            _positive("fin_pitch", self.fin_pitch)
            _positive("fin_thickness", self.fin_thickness)

    @property
    def d_i(self):
        """内径 d_i = d_o - 2δ，m。"""
        return self.d_o - 2.0 * self.wall_thickness


@dataclass(frozen=True)
class PlateGeometry:
    """板式几何。长度 m，波纹倾角 rad。本期不能进入求解。"""

    plate_width: float
    plate_height: float
    plate_spacing: float
    n_plates: int
    corrugation_angle: float
    corrugation_pitch: float
    corrugation_depth: float

    def __post_init__(self):
        _positive("plate_width", self.plate_width)
        _positive("plate_height", self.plate_height)
        _positive("plate_spacing", self.plate_spacing)
        _positive_int("n_plates", self.n_plates)
        _positive("corrugation_pitch", self.corrugation_pitch)
        _positive("corrugation_depth", self.corrugation_depth)
        if (
            not math.isfinite(self.corrugation_angle)
            or self.corrugation_angle <= 0.0
            or self.corrugation_angle >= math.pi / 2.0
        ):
            raise OutOfRangeError(
                "corrugation_angle",
                self.corrugation_angle,
                "(0, π/2) rad",
                "波纹倾角",
            )


def _positive(name, value):
    if type(value) is not float and type(value) is not int:
        raise InputError(f"{name} 必须是实数")
    if not math.isfinite(value) or value <= 0.0:
        raise OutOfRangeError(name, value, "> 0", "几何尺寸")


def _positive_int(name, value):
    if type(value) is not int or value < 1:
        raise InputError(f"{name} 必须是正整数")
