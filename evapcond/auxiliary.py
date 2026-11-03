"""风机、水泵和补水。

风量 = v_f × 迎风面积。
风机全压 = 湿管束压降 + (ζ_de + ζ_lv + ζ_st) ρ_a v_f² / 2。
喷淋水量 = Γ × 2 × N_t × L。
扬程 = p_noz / (ρ_w g) + H_lift + λ (L/D) V²/(2g) + Σζ V²/(2g)。
局部阻力系数以管内流速的速度头为基准。
轴功率 = 有效功率 / η。风机有效功率为体积流量乘全压，水泵为质量流量乘 g 乘扬程。
补水量 = 蒸发量 + 排污量 + 风吹损失。
蒸发量 = m_dry (w_out − w_in)，排污量 = 蒸发量 / (N_cyc − 1)，
风吹损失 = drift_rate × 喷淋水量。

ρ_a、μ_a、ρ_w、μ_w 由调用方传入。本模块不选择空气或水的取值截面。
"""

import math

from evapcond.airside import gamma_m_from_gamma, spray_mass_flow
from evapcond.correlations.bundle_pressure import (
    EQUILATERAL_K1_NOTE,
    WET_ESTIMATE_NOTE,
    ZUKAUSKAS_BASIS_NOTE,
    dry_bundle_pressure_drop,
    euler_number,
    row_correction,
    wet_pressure_drop,
)
from evapcond.correlations.pipe_friction import darcy_friction_factor
from evapcond.correlations.pressure_drop import STANDARD_GRAVITY
from evapcond.errors import InputError, OutOfRangeError
from evapcond.geometry.plate import require_plate_calculation
from evapcond.geometry.tube import (
    face_area,
    require_supported_surface,
    velocity_max_over_face,
)
from evapcond.models import AuxInput, AuxResult, PlateGeometry, TubeGeometry

DRIFT_ENGINEERING_NOTE = "风吹损失按喷淋水量计。此为工程取值，非标准强制条款"


def evaluate_auxiliary(
    geometry,
    v_face,
    gamma,
    rho_air,
    mu_air,
    rho_water,
    mu_water,
    m_dry_air,
    w_in,
    w_out,
    aux,
):
    """计算风机、水泵和补水。几何不是光管时按未确认关联式拒绝。"""
    if isinstance(geometry, PlateGeometry):
        require_plate_calculation(geometry)
    if not isinstance(geometry, TubeGeometry):
        raise InputError("需要 TubeGeometry 或 PlateGeometry")
    require_supported_surface(geometry.surface_type)
    if not isinstance(aux, AuxInput):
        raise InputError("需要 AuxInput")
    if not math.isfinite(v_face) or v_face <= 0.0:
        raise InputError("v_f 必须大于 0")
    _positive("rho_a", rho_air)
    _positive("mu_a", mu_air)
    _positive("rho_w", rho_water)
    _positive("mu_w", mu_water)
    if not math.isfinite(m_dry_air) or m_dry_air <= 0.0:
        raise InputError("m_dry_air 必须大于 0")
    _humidity("w_in", w_in)
    _humidity("w_out", w_out)

    area = face_area(geometry)
    v_max = v_face * velocity_max_over_face(geometry)
    reynolds = rho_air * v_max * geometry.d_o / mu_air
    euler, euler_record = euler_number(geometry.S_T / geometry.d_o, reynolds)
    c2, c2_record = row_correction(geometry.N_r)
    dp_dry = dry_bundle_pressure_drop(rho_air, v_max, geometry.N_r, euler, c2)
    gamma_m = gamma_m_from_gamma(gamma, geometry.d_o, geometry.S_T)
    dp_wet, wet_record = wet_pressure_drop(dp_dry, gamma_m, geometry.d_o)

    accessory = (
        (aux.zeta_de + aux.zeta_lv + aux.zeta_st) * rho_air * v_face**2 / 2.0
    )
    air_volume_flow = v_face * area
    fan_pressure = dp_wet + accessory
    fan_power = air_volume_flow * fan_pressure / aux.eta_fan

    spray = spray_mass_flow(gamma, geometry.N_t, geometry.L)
    pump_volume_flow = spray / rho_water
    pipe_area = math.pi * aux.pipe_diameter**2 / 4.0
    pipe_velocity = pump_volume_flow / pipe_area
    pipe_reynolds = rho_water * pipe_velocity * aux.pipe_diameter / mu_water
    darcy, darcy_record = darcy_friction_factor(
        pipe_reynolds,
        aux.pipe_roughness,
        aux.pipe_diameter,
    )
    velocity_head = pipe_velocity**2 / (2.0 * STANDARD_GRAVITY)
    friction_head = darcy * (aux.pipe_length / aux.pipe_diameter) * velocity_head
    local_head = aux.zeta_pipe * velocity_head
    nozzle_head = aux.p_noz / (rho_water * STANDARD_GRAVITY)
    pump_head = nozzle_head + aux.H_lift + friction_head + local_head
    pump_power = spray * STANDARD_GRAVITY * pump_head / aux.eta_pump

    evaporated = m_dry_air * (w_out - w_in)
    blowdown = evaporated / (aux.N_cyc - 1.0)
    drift = aux.drift_rate * spray
    makeup = evaporated + blowdown + drift
    _finite_result(
        air_volume_flow,
        fan_pressure,
        fan_power,
        pump_volume_flow,
        pump_head,
        pump_power,
        evaporated,
        blowdown,
        drift,
        makeup,
    )
    return AuxResult(
        air_volume_flow=air_volume_flow,
        fan_pressure=fan_pressure,
        fan_power=fan_power,
        spray_mass_flow=spray,
        pump_volume_flow=pump_volume_flow,
        pump_head=pump_head,
        pump_power=pump_power,
        m_evap=evaporated,
        m_blowdown=blowdown,
        m_drift=drift,
        m_makeup=makeup,
        delta_p_dry=dp_dry,
        delta_p_wet=dp_wet,
        delta_p_accessories=accessory,
        darcy_lambda=darcy,
        estimated_wet_correction=True,
        correlations=(euler_record, c2_record, wet_record, darcy_record),
        diagnostics=(
            ZUKAUSKAS_BASIS_NOTE,
            EQUILATERAL_K1_NOTE,
            WET_ESTIMATE_NOTE,
            DRIFT_ENGINEERING_NOTE,
        ),
        warnings=(),
    )


def _humidity(name, value):
    if not math.isfinite(value) or value < 0.0:
        raise OutOfRangeError(name, value, ">= 0 kg/kg", "湿空气含湿量")


def _positive(name, value):
    if not math.isfinite(value) or value <= 0.0:
        raise OutOfRangeError(name, value, "> 0", "辅助计算的密度或粘度")


def _finite_result(*values):
    for value in values:
        if not math.isfinite(value):
            raise OutOfRangeError("auxiliary", value, "有限值", "风机、水泵或补水结果")
