"""校核模式。传热调用求解器，辅机调用 evaluate_auxiliary。

管束压降和附件阻力用进口湿空气的密度、粘度。迎面风速已经按这个状态
折算干空气流量，最窄截面风速是该迎面风速的几何倍数。
水泵用求解得到的循环喷淋水温，压力取进口空气压力。
这两处取值截面补充材料没有指定。
"""

import math

from evapcond.airside import gamma_m_from_gamma, saturation_humidity
from evapcond.auxiliary import evaluate_auxiliary
from evapcond.correlations.film_air import (
    MIZUSHINA_NOTE,
    air_convection_coefficient,
    bosnjakovic_lewis_factor,
)
from evapcond.errors import InputError, OutOfRangeError
from evapcond.geometry.plate import require_plate_calculation
from evapcond.geometry.tube import face_area, require_supported_surface
from evapcond.models import (
    AuxInput,
    PlateGeometry,
    RatingInput,
    RatingResult,
    SolverConfig,
    TubeGeometry,
)
from evapcond.properties.humid_air import HumidAirState, humid_air_state
from evapcond.properties.refrigerant import (
    R404A_PSEUDOPURE_NOTE,
    check_condensing_temperature,
    coolprop_fluid_name,
    enthalpy_pt,
    saturation_pressure,
    saturation_temperature,
    vapor_enthalpy,
)
from evapcond.refside import refrigerant_state
from evapcond.properties.water import density, viscosity
from evapcond.solver import solve

# 与制冷剂侧单相闪蒸带宽相同。落在带内时进口没有独立干度，按饱和蒸气。
SATURATED_VAPOR_BAND_K = 1e-4
INLET_SATURATION_AGREEMENT_K = 1e-3

INLET_AIR_PROPERTY_NOTE = (
    "管束压降与附件阻力使用进口湿空气的密度和粘度，"
    "与由迎面风速计算干空气流量时的状态相同。"
)
SPRAY_WATER_PROPERTY_NOTE = "水泵物性使用求解得到的循环喷淋水温，压力取进口空气压力。"
SATURATED_VAPOR_INLET_NOTE = (
    "进口温度与饱和温度之差不超过 1e-4 K，进口焓按饱和蒸气计算。"
)


def run(rating, config=None, progress_cb=None, cancel_event=None):
    """校核一台给定几何的蒸发式冷凝器。"""
    if not isinstance(rating, RatingInput):
        raise InputError("需要 RatingInput")
    if config is None:
        config = SolverConfig()
    if not isinstance(config, SolverConfig):
        raise InputError("config 必须是 SolverConfig")
    _require_geometry(rating.geometry)
    if not isinstance(rating.aux, AuxInput):
        raise InputError("需要 AuxInput")
    if not isinstance(rating.air, HumidAirState):
        raise InputError("空气进口必须是湿空气状态")
    coolprop_fluid_name(rating.refrigerant)
    _missing_fields(rating)
    _conflicting_fields(rating)
    if not math.isfinite(rating.m_ref) or rating.m_ref <= 0.0:
        raise InputError("制冷剂流量必须大于 0")
    v_face = resolve_face_velocity(
        rating.geometry, rating.v_face, rating.air_volume_flow
    )
    gamma = resolve_spray_density(rating.geometry, rating.gamma, rating.m_spray)
    pressure, enthalpy, saturated_vapor = refrigerant_inlet_enthalpy(
        rating.refrigerant, rating.T_in, rating.p_in, rating.T_sat_in
    )
    solved = solve(
        rating.geometry,
        rating.refrigerant,
        rating.m_ref,
        pressure,
        enthalpy,
        rating.air,
        v_face,
        gamma,
        config=config,
        progress_cb=progress_cb,
        cancel_event=cancel_event,
        le_f=rating.le_f,
    )
    rho_water = density(solved.T_spray, rating.air.p)
    mu_water = viscosity(solved.T_spray, rating.air.p)
    auxiliary = evaluate_auxiliary(
        rating.geometry,
        v_face,
        gamma,
        rating.air.rho,
        rating.air.mu,
        rho_water,
        mu_water,
        solved.m_dry,
        rating.air.w,
        solved.air_out.w,
        rating.aux,
    )
    outlet = refrigerant_state(rating.refrigerant, solved.p_out, solved.h_ref_out)
    quality, subcooling, superheat = _outlet_measures(outlet)
    film_temperatures = [segment.T_w for segment in solved.segments]
    film_temperatures.append(solved.T_spray)
    return RatingResult(
        Q=solved.Q,
        T_ref_out=outlet.T,
        p_ref_out=outlet.p,
        h_ref_in=enthalpy,
        h_ref_out=solved.h_ref_out,
        region_out=outlet.region,
        x_out=quality,
        subcooling=subcooling,
        superheat=superheat,
        T_air_out=solved.air_out.T_db,
        w_air_out=solved.air_out.w,
        i_air_out=solved.air_out.h,
        T_film_min=min(film_temperatures),
        T_film_max=max(film_temperatures),
        h_m=mean_mass_transfer_coefficient(
            rating.geometry, solved.segments, rating.air.p, rating.le_f
        ),
        resistances=solved.resistances,
        auxiliary=auxiliary,
        segments=solved.segments,
        convergence=solved.convergence,
        correlations=_merge_records(solved.correlations, auxiliary.correlations),
        diagnostics=_diagnostics(rating.refrigerant, saturated_vapor, auxiliary.diagnostics),
        warnings=solved.warnings + auxiliary.warnings,
    )


def resolve_face_velocity(geometry, v_face, air_volume_flow):
    """由迎面风速或风量得到 v_f，m/s。风量是 m³/s。"""
    if v_face is not None and air_volume_flow is not None:
        raise InputError("风量与 v_f 只能填写一个")
    if v_face is None and air_volume_flow is None:
        raise InputError("缺少必填字段：v_f 或风量")
    if v_face is None:
        if not math.isfinite(air_volume_flow) or air_volume_flow <= 0.0:
            raise InputError("风量必须大于 0")
        return air_volume_flow / face_area(geometry)
    if not math.isfinite(v_face) or v_face <= 0.0:
        raise InputError("v_f 必须大于 0")
    return float(v_face)


def resolve_spray_density(geometry, gamma, m_spray):
    """由 Γ 或喷淋水量得到单侧线密度，kg/(m·s)。"""
    if gamma is not None and m_spray is not None:
        raise InputError("喷淋水量与 Γ 只能填写一个")
    if gamma is None and m_spray is None:
        raise InputError("缺少必填字段：Γ 或喷淋水量")
    if gamma is None:
        if not math.isfinite(m_spray) or m_spray <= 0.0:
            raise InputError("喷淋水量必须大于 0")
        return m_spray / (2.0 * geometry.N_t * geometry.L)
    if not math.isfinite(gamma) or gamma <= 0.0:
        raise InputError("Γ 必须大于 0")
    return float(gamma)


def refrigerant_inlet_enthalpy(refrigerant, T_in, p_in=None, T_sat_in=None):
    """进口压力与比焓。温差不超过 1e-4 K 时焓取饱和蒸气焓。"""
    coolprop_fluid_name(refrigerant)
    if T_in is None or not math.isfinite(T_in):
        raise InputError("缺少必填字段：进口温度")
    if p_in is None and T_sat_in is None:
        raise InputError("缺少必填字段：进口压力或进口饱和温度")
    if p_in is not None and (not math.isfinite(p_in) or p_in <= 0.0):
        raise OutOfRangeError("p_in", p_in, "> 0 Pa", "制冷剂进口压力")
    if T_sat_in is not None and not math.isfinite(T_sat_in):
        raise OutOfRangeError("T_sat_in", T_sat_in, "有限温度", "制冷剂进口饱和温度")
    if p_in is None:
        check_condensing_temperature(refrigerant, T_sat_in)
        pressure = saturation_pressure(refrigerant, T_sat_in)
    else:
        pressure = float(p_in)
        t_sat = saturation_temperature(refrigerant, pressure)
        check_condensing_temperature(refrigerant, t_sat)
        if (
            T_sat_in is not None
            and abs(T_sat_in - t_sat) > INLET_SATURATION_AGREEMENT_K
        ):
            raise InputError(
                "进口压力与进口饱和温度不一致："
                f"由压力得到 {t_sat} K，输入为 {T_sat_in} K"
            )
    t_sat = saturation_temperature(refrigerant, pressure)
    if abs(T_in - t_sat) <= SATURATED_VAPOR_BAND_K:
        return pressure, vapor_enthalpy(refrigerant, t_sat), True
    return pressure, enthalpy_pt(refrigerant, T_in, pressure), False


def mean_mass_transfer_coefficient(geometry, segments, pressure, le_f=None):
    """各控制容积 h_m 的算术平均。分段长度相同，因此也是面积加权平均。"""
    if not segments:
        raise InputError("没有可用于平均传质系数的控制容积")
    n_l = max(segment.seg for segment in segments)
    d_l = geometry.L / n_l
    values = []
    for segment in segments:
        gamma = segment.m_w / (2.0 * d_l)
        gamma_m = gamma_m_from_gamma(gamma, geometry.d_o, geometry.S_T)
        h_c, _ = air_convection_coefficient(gamma_m, geometry.d_o)
        state = humid_air_state(pressure, T_db=segment.T_a, w=segment.w_a)
        w_s = saturation_humidity(segment.T_w, pressure)
        lewis, _ = bosnjakovic_lewis_factor(w_s, segment.w_a, le_f=le_f)
        values.append(h_c / (state.cp * lewis))
    return sum(values) / len(values)


def _outlet_measures(state):
    if state.region == "subcooled":
        return None, state.T_sat - state.T, None
    if state.region == "superheated":
        return None, None, state.T - state.T_sat
    return state.x, None, None


def _diagnostics(refrigerant, saturated_vapor, auxiliary_diagnostics):
    notes = [MIZUSHINA_NOTE, INLET_AIR_PROPERTY_NOTE, SPRAY_WATER_PROPERTY_NOTE]
    if refrigerant == "R404A":
        notes.append(R404A_PSEUDOPURE_NOTE)
    if saturated_vapor:
        notes.append(SATURATED_VAPOR_INLET_NOTE)
    notes.extend(auxiliary_diagnostics)
    return tuple(notes)


def _merge_records(*groups):
    seen = set()
    merged = []
    for group in groups:
        for record in group:
            if record.name in seen:
                continue
            seen.add(record.name)
            merged.append(record)
    return tuple(merged)


def _require_geometry(geometry):
    if isinstance(geometry, PlateGeometry):
        require_plate_calculation(geometry)
    if not isinstance(geometry, TubeGeometry):
        raise InputError("需要 TubeGeometry 或 PlateGeometry")
    require_supported_surface(geometry.surface_type)


def _missing_fields(rating):
    missing = []
    if rating.v_face is None and rating.air_volume_flow is None:
        missing.append("v_f 或风量")
    if rating.gamma is None and rating.m_spray is None:
        missing.append("Γ 或喷淋水量")
    if rating.p_in is None and rating.T_sat_in is None:
        missing.append("进口压力或进口饱和温度")
    if rating.T_in is None:
        missing.append("进口温度")
    if missing:
        raise InputError("缺少必填字段：" + "、".join(missing))


def _conflicting_fields(rating):
    if rating.v_face is not None and rating.air_volume_flow is not None:
        raise InputError("风量与 v_f 只能填写一个")
    if rating.gamma is not None and rating.m_spray is not None:
        raise InputError("喷淋水量与 Γ 只能填写一个")
