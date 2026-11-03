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


def _real_number(name, value):
    if type(value) is not float and type(value) is not int:
        raise InputError(f"{name} 必须是实数")
    if not math.isfinite(value):
        raise OutOfRangeError(name, value, "有限实数", "辅助输入")


def _at_least_zero(name, value):
    _real_number(name, value)
    if value < 0.0:
        raise OutOfRangeError(name, value, ">= 0", "辅助输入")


def _unit_interval(name, value):
    _real_number(name, value)
    if value <= 0.0 or value > 1.0:
        raise OutOfRangeError(name, value, "(0, 1]", "轴功率 = 有效功率 / η")


@dataclass(frozen=True)
class CorrelationMeta:
    """关联式的文献与适用范围。reported_deviation 没有数字时写明未给出。"""

    name: str
    citation: str
    applicability: str
    reported_deviation: str


@dataclass(frozen=True)
class CorrelationRecord:
    """一次关联式调用。parameters 为 (参数名, 数值) 对。"""

    name: str
    citation: str
    applicability: str
    parameters: tuple


@dataclass(frozen=True)
class SolverConfig:
    """分段目标数、迭代上限和松弛因子。三项收敛判据不能在这里放宽。"""

    n_cv_target: int = 40
    max_iterations: int = 500
    relaxation: float = 1.0

    def __post_init__(self):
        if type(self.n_cv_target) is not int or self.n_cv_target < 20:
            raise OutOfRangeError(
                "N_cv_target",
                self.n_cv_target,
                ">= 20",
                "规格：控制容积不得少于 20",
            )
        if type(self.max_iterations) is not int or self.max_iterations < 1:
            raise OutOfRangeError(
                "max_iterations",
                self.max_iterations,
                ">= 1",
                "求解器迭代上限",
            )
        if (type(self.relaxation) is not float and type(self.relaxation) is not int) or (
            not math.isfinite(self.relaxation)
            or self.relaxation <= 0.0
            or self.relaxation > 1.0
        ):
            raise OutOfRangeError("relaxation", self.relaxation, "(0, 1]", "求解器松弛因子")


@dataclass(frozen=True)
class SegmentState:
    """一个控制容积。行号自顶排起算，段号沿管长的几何方向，都从 1 起。"""

    row: int
    seg: int
    region: str
    T_ref: float
    p: float
    x: float | None
    h_ref: float
    T_w: float
    m_w: float
    T_a: float
    w_a: float
    i_a: float
    dQ_ref: float
    dQ_s: float
    dQ_l: float
    R_ref: float
    R_wall: float
    R_out: float


@dataclass(frozen=True)
class ResistanceSummary:
    """热阻占比与按管外面积定义的 K。R 为按换热量加权的段热阻。"""

    share_ref: float
    share_wall: float
    share_out: float
    K: float
    R_ref: float
    R_wall: float
    R_out: float


@dataclass(frozen=True)
class ConvergenceInfo:
    """最后一轮的三项残差。空气焓残差单位是 J/kg。"""

    iterations: int
    heat_relative: float
    film_temperature: float
    air_enthalpy: float


@dataclass(frozen=True)
class AuxInput:
    """风机、水泵和补水的输入。压力 Pa，长度 m，阻力系数无量纲。

    eta_fan、eta_pump、N_cyc、drift_rate 是可覆盖的工程默认值。
    drift_rate 是风吹损失与喷淋水量之比，默认 0.01% = 0.0001。
    """

    zeta_de: float
    zeta_lv: float
    zeta_st: float
    p_noz: float
    H_lift: float
    pipe_length: float
    pipe_diameter: float
    zeta_pipe: float
    pipe_roughness: float
    eta_fan: float = 0.65
    eta_pump: float = 0.70
    N_cyc: float = 3.0
    drift_rate: float = 0.0001

    def __post_init__(self):
        for name in (
            "zeta_de",
            "zeta_lv",
            "zeta_st",
            "zeta_pipe",
            "pipe_roughness",
            "H_lift",
            "p_noz",
            "drift_rate",
        ):
            _at_least_zero(name, getattr(self, name))
        _positive("pipe_length", self.pipe_length)
        _positive("pipe_diameter", self.pipe_diameter)
        for name in ("eta_fan", "eta_pump"):
            _unit_interval(name, getattr(self, name))
        _real_number("N_cyc", self.N_cyc)
        if self.N_cyc <= 1.0:
            raise OutOfRangeError(
                "N_cyc",
                self.N_cyc,
                "> 1",
                "排污量 = 蒸发量 / (N_cyc - 1)",
            )


@dataclass(frozen=True)
class AuxResult:
    """辅机结果。体积流量 m³/s，质量流量 kg/s，压力 Pa，扬程 m，功率 W。"""

    air_volume_flow: float
    fan_pressure: float
    fan_power: float
    spray_mass_flow: float
    pump_volume_flow: float
    pump_head: float
    pump_power: float
    m_evap: float
    m_blowdown: float
    m_drift: float
    m_makeup: float
    delta_p_dry: float
    delta_p_wet: float
    delta_p_accessories: float
    darcy_lambda: float
    estimated_wet_correction: bool
    correlations: tuple
    diagnostics: tuple
    warnings: tuple


@dataclass(frozen=True)
class RatingInput:
    """校核输入。压力 Pa，温度 K，流量 kg/s，风速 m/s。

    风量与 v_face 二选一，喷淋水量与 gamma 二选一。
    p_in 与 T_sat_in 至少给一个，同时给时必须对应同一饱和状态。
    """

    geometry: object
    refrigerant: str
    m_ref: float
    T_in: float
    air: object
    aux: AuxInput
    p_in: float | None = None
    T_sat_in: float | None = None
    v_face: float | None = None
    air_volume_flow: float | None = None
    gamma: float | None = None
    m_spray: float | None = None
    le_f: float | None = None


@dataclass(frozen=True)
class RatingResult:
    """校核结果。温度 K，压力 Pa，焓 J/kg，h_m 为 kg/(m²·s)。"""

    Q: float
    T_ref_out: float
    p_ref_out: float
    h_ref_in: float
    h_ref_out: float
    region_out: str
    x_out: float | None
    subcooling: float | None
    superheat: float | None
    T_air_out: float
    w_air_out: float
    i_air_out: float
    T_film_min: float
    T_film_max: float
    h_m: float
    resistances: ResistanceSummary
    auxiliary: AuxResult
    segments: tuple
    convergence: ConvergenceInfo
    correlations: tuple
    diagnostics: tuple
    warnings: tuple


@dataclass(frozen=True)
class DesignInput:
    """设计输入。热量 W，温度 K，风速 m/s。几何候选用 SI 单位。"""

    Q: float
    refrigerant: str
    T_k: float
    air: object
    v_face_max: float
    aux: AuxInput
    surface_type: str = "tube_plain"
    superheat: float = 0.0
    subcooling: float = 0.0
    d_o: tuple = (0.01905, 0.025, 0.032)
    wall_thickness: float = 0.002
    k_w: float = 63.9
    transverse_pitch_ratio: tuple = (2.0, 2.5)
    longitudinal_pitch_ratio: tuple = (1.5, 2.0)
    gamma: tuple | None = None
    gamma_min: float | None = None
    gamma_max: float | None = None
    lengths: tuple = (2.0, 4.0, 6.0)
    face_velocity_factor: tuple = (0.6, 0.8, 1.0)
    rows: tuple = (4, 8, 12, 16, 20, 24, 28)
    le_f: float | None = None
    exhaustive: bool = False

    def __post_init__(self):
        if not isinstance(self.aux, AuxInput):
            raise InputError("需要 AuxInput")
        _positive("Q", self.Q)
        _positive("v_face_max", self.v_face_max)
        _positive("wall_thickness", self.wall_thickness)
        _positive("k_w", self.k_w)
        _at_least_zero("superheat", self.superheat)
        _at_least_zero("subcooling", self.subcooling)
        if self.surface_type not in ("tube_plain", "tube_lowfin", "plate"):
            raise InputError(
                f"未知表面类型 {self.surface_type}。有效值：tube_plain、tube_lowfin、plate"
            )
        if not self.d_o or not self.lengths or not self.rows:
            raise InputError("几何候选列表为空")
        if not self.face_velocity_factor:
            raise InputError("迎面风速候选列表为空")
        if self.exhaustive not in (True, False):
            raise InputError("exhaustive 必须是布尔值")


@dataclass(frozen=True)
class DesignResult:
    """设计结果。传热与辅机的明细在 rating 里。"""

    geometry: object
    v_face: float
    gamma: float
    area: float
    face_area: float
    rating: RatingResult
    warnings: tuple
    diagnostics: tuple
    coarse_count: int
    refined_count: int
    m_ref: float
    T_in: float
