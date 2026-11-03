"""设计模式。粗网格、贴边外扩和局部细化。

每个候选先剔除关联式必然越界的组合，再求单回路流量。
求根沿用上一轮水膜温度，区间端点只计算一次。
不同几何组同时计算，每组自带物性缓存，组之间不共享可变状态。
流量只求到恰好达到目标出口。回路数仍按规格取整后再校核。
"""

import math
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, replace

from scipy.optimize import brentq

from evapcond.airside import gamma_m_from_gamma
from evapcond.correlations.bundle_pressure import euler_number
from evapcond.correlations.film_air import (
    MIZUSHINA_RATIO_MAX,
    MIZUSHINA_RATIO_MIN,
    air_convection_coefficient,
)
from evapcond.errors import (
    CancelledError,
    ConvergenceError,
    InfeasibleDesignError,
    InputError,
    OutOfRangeError,
)
from evapcond.geometry.candidates import (
    EXHAUSTIVE_LENGTHS,
    EXHAUSTIVE_ROWS,
    SPEC_ROW_LIMIT,
    expanded_lengths,
    expanded_rows,
    length_edge_warning,
    row_edge_warning,
)
from evapcond.geometry.tube import (
    face_area,
    outside_area,
    require_supported_surface,
    velocity_max_over_face,
    with_tube_count,
)
from evapcond.models import DesignInput, DesignResult, SolverConfig, TubeGeometry
from evapcond.properties.humid_air import HumidAirState
from evapcond.properties.refrigerant import (
    check_condensing_temperature,
    enthalpy_pt,
    liquid_enthalpy,
    saturation_pressure,
    saturation_temperature,
    vapor_enthalpy,
)
from evapcond.rating import run as rate
from evapcond.solver import solve

NON_EXHAUSTIVE_NOTE = (
    "设计结果基于粗网格搜索（2268点）与局部细化寻优，非全局穷举。"
    "若需绝对全局最优，请手动开启 exhaustive 模式。"
)
_ROOT_MULTIPLIERS = (1.0, 0.7, 1.4, 0.45, 2.2, 0.25, 4.0, 0.1, 8.0, 0.05, 16.0, 0.02)
_DEFAULT_FLOW_GUESS = 0.02


@dataclass(frozen=True)
class _Group:
    tube: TubeGeometry
    rows: tuple
    gamma: float
    v_face: float


@dataclass(frozen=True)
class _Common:
    refrigerant: str
    Q: float
    T_k: float
    superheat: float
    subcooling: float
    p_in: float
    h_in: float
    h_out: float
    m_ref: float
    air: object
    aux: object
    le_f: float | None
    config: SolverConfig


@dataclass(frozen=True)
class _Hit:
    tube: TubeGeometry
    v_face: float
    gamma: float
    area: float
    power: float
    m_c: float
    rating: object


def run(design, config=None, progress_cb=None, cancel_event=None, *, workers=None, refine=True):
    """搜索传热面积最小的可行设计。面积相同时取风机与水泵功率之和较小者。"""
    if not isinstance(design, DesignInput):
        raise InputError("需要 DesignInput")
    if config is None:
        config = SolverConfig()
    if not isinstance(config, SolverConfig):
        raise InputError("config 必须是 SolverConfig")
    validate(design)
    common = _common(design, config)
    groups = _coarse_groups(design)
    if not groups:
        raise InfeasibleDesignError(())
    if workers is None:
        workers = min(8, os.cpu_count() or 1)
    total = _candidate_count(groups)
    hits, warnings = _run_groups(
        groups, common, workers, progress_cb, cancel_event, 0, total
    )
    coarse_count = total
    if not hits:
        raise InfeasibleDesignError(_relaxation_suggestions(design, config, workers))
    ordered = _ordered(hits)
    notes = []
    if coarse_count == 2268 and not design.exhaustive:
        notes.append(NON_EXHAUSTIVE_NOTE)
    refined_count = 0
    if refine:
        for note in _edge_notes(ordered[0]):
            notes.append(note)
            print(note)
        extra, refined_count = _refinement_groups(design, ordered, _seen(hits))
        if extra:
            more, more_warnings = _run_groups(
                extra,
                common,
                workers,
                progress_cb,
                cancel_event,
                coarse_count,
                coarse_count + refined_count,
            )
            hits.extend(more)
            warnings.extend(more_warnings)
            ordered = _ordered(hits)
    best = ordered[0]
    diagnostics = notes + list(best.rating.diagnostics)
    return DesignResult(
        geometry=best.tube,
        v_face=best.v_face,
        gamma=best.gamma,
        area=best.area,
        face_area=face_area(best.tube),
        rating=best.rating,
        warnings=tuple(warnings) + best.rating.warnings,
        diagnostics=tuple(diagnostics),
        coarse_count=coarse_count,
        refined_count=refined_count,
        m_ref=common.m_ref,
        T_in=common.T_k + common.superheat,
    )


def validate(design):
    """设计输入在进入搜索前的检查。"""
    _validate(design)


def _validate(design):
    require_supported_surface(design.surface_type)
    if not isinstance(design.air, HumidAirState):
        raise InputError("空气进口必须是湿空气状态")
    check_condensing_temperature(design.refrigerant, design.T_k)
    if design.air.T_wb >= design.air.T_db or design.air.T_wb >= design.T_k:
        raise InputError("T_wb_in 必须小于 T_db_in 且小于 T_k")


def _common(design, config):
    pressure = saturation_pressure(design.refrigerant, design.T_k)
    if design.superheat <= 1e-4:
        h_in = vapor_enthalpy(design.refrigerant, design.T_k)
    else:
        h_in = enthalpy_pt(design.refrigerant, design.T_k + design.superheat, pressure)
    if design.subcooling <= 1e-4:
        h_out = liquid_enthalpy(design.refrigerant, design.T_k)
    else:
        h_out = enthalpy_pt(
            design.refrigerant, design.T_k - design.subcooling, pressure
        )
    if h_in <= h_out:
        raise InputError("进口焓必须高于目标出口焓")
    return _Common(
        refrigerant=design.refrigerant,
        Q=design.Q,
        T_k=design.T_k,
        superheat=design.superheat,
        subcooling=design.subcooling,
        p_in=pressure,
        h_in=h_in,
        h_out=h_out,
        m_ref=design.Q / (h_in - h_out),
        air=design.air,
        aux=design.aux,
        le_f=design.le_f,
        config=config,
    )


def _axes(design):
    if design.exhaustive:
        return EXHAUSTIVE_LENGTHS, EXHAUSTIVE_ROWS
    return tuple(design.lengths), tuple(int(row) for row in design.rows)


def _coarse_groups(design):
    lengths, rows = _axes(design)
    groups = []
    for diameter in design.d_o:
        for transverse in design.transverse_pitch_ratio:
            for longitudinal in design.longitudinal_pitch_ratio:
                pitch = float(transverse) * float(diameter)
                gammas = _gammas(design, pitch)
                for length in lengths:
                    tube = TubeGeometry(
                        surface_type="tube_plain",
                        d_o=float(diameter),
                        wall_thickness=float(design.wall_thickness),
                        k_w=float(design.k_w),
                        S_T=pitch,
                        S_L=float(longitudinal) * float(diameter),
                        N_r=int(rows[0]),
                        N_t=1,
                        L=float(length),
                    )
                    for gamma in gammas:
                        for factor in design.face_velocity_factor:
                            velocity = float(factor) * design.v_face_max
                            if velocity <= 0.0:
                                continue
                            groups.append(_Group(tube, rows, float(gamma), velocity))
    return tuple(groups)


def _gammas(design, pitch):
    if design.gamma is not None:
        return tuple(float(value) for value in design.gamma)
    low = MIZUSHINA_RATIO_MIN * pitch
    high = MIZUSHINA_RATIO_MAX * pitch
    if design.gamma_min is not None:
        low = max(low, design.gamma_min)
    if design.gamma_max is not None:
        high = min(high, design.gamma_max)
    if high <= low:
        return ()
    span = high - low
    return tuple(low + span * index / 4.0 for index in (1, 2, 3))


def _candidate_count(groups):
    return sum(len(group.rows) for group in groups)


def _run_groups(groups, common, workers, progress_cb, cancel_event, done, total):
    if workers <= 1:
        return _run_serial(groups, common, progress_cb, cancel_event, done, total)
    hits = []
    warnings = []
    payloads = [(group, common) for group in groups]
    pool = ProcessPoolExecutor(max_workers=workers)
    try:
        futures = [pool.submit(_evaluate_group, payload) for payload in payloads]
        for future in as_completed(futures):
            if cancel_event is not None and cancel_event.is_set():
                pool.shutdown(wait=False, cancel_futures=True)
                raise CancelledError("已取消")
            found, notes, count = future.result()
            hits.extend(found)
            warnings.extend(notes)
            done += count
            if progress_cb is not None:
                progress_cb(done, total, f"已评估候选 {done}/{total}")
    finally:
        pool.shutdown(wait=True)
    return hits, warnings


def _run_serial(groups, common, progress_cb, cancel_event, done, total):
    hits = []
    warnings = []
    for group in groups:
        if cancel_event is not None and cancel_event.is_set():
            raise CancelledError("已取消")
        found, notes, count = _evaluate_group((group, common))
        hits.extend(found)
        warnings.extend(notes)
        done += count
        if progress_cb is not None:
            progress_cb(done, total, f"已评估候选 {done}/{total}")
    return hits, warnings


def _evaluate_group(payload):
    group, common = payload
    hint = None
    found = []
    warnings = []
    for n_r in group.rows:
        tube = replace(group.tube, N_r=int(n_r))
        try:
            _precheck(tube, group.v_face, group.gamma, common.air)
            m_c = _circuit_flow(tube, common, group.v_face, group.gamma, hint)
        except (OutOfRangeError, ConvergenceError, InputError) as exc:
            warnings.append(str(exc))
            continue
        circuits = max(1, math.ceil(common.m_ref / m_c - 1e-12))
        sized = with_tube_count(tube, circuits)
        try:
            rated = _rate_candidate(sized, common, group.v_face, group.gamma)
        except (OutOfRangeError, ConvergenceError, InputError) as exc:
            warnings.append(str(exc))
            continue
        if rated.Q < common.Q:
            warnings.append(
                f"N_r={n_r}、L={tube.L} m 的校核换热量 {rated.Q} W 低于 Q_k"
            )
            continue
        power = rated.auxiliary.fan_power + rated.auxiliary.pump_power
        found.append(
            _Hit(
                tube=sized,
                v_face=group.v_face,
                gamma=group.gamma,
                area=outside_area(sized),
                power=power,
                m_c=m_c,
                rating=rated,
            )
        )
        hint = m_c
    return found, warnings, len(group.rows)


def _precheck(tube, v_face, gamma, air):
    gamma_m = gamma_m_from_gamma(gamma, tube.d_o, tube.S_T)
    air_convection_coefficient(gamma_m, tube.d_o)
    reynolds = air.rho * v_face * velocity_max_over_face(tube) * tube.d_o / air.mu
    euler_number(tube.S_T / tube.d_o, reynolds)


def _circuit_flow(tube, common, v_face, gamma, hint):
    film = None
    cache = {}

    def residual(mass_flow):
        nonlocal film
        key = float(mass_flow)
        cached = cache.get(key)
        if cached is not None:
            return cached
        result = solve(
            tube,
            common.refrigerant,
            key,
            common.p_in,
            common.h_in,
            common.air,
            v_face,
            gamma,
            config=common.config,
            le_f=common.le_f,
            initial_film=film,
        )
        film = result.film
        value = result.h_ref_out - _target_exit_enthalpy(common, result.p_out)
        cache[key] = value
        return value

    guess = hint if hint is not None and hint > 0.0 else _DEFAULT_FLOW_GUESS
    low = None
    high = None
    low_value = None
    high_value = None
    for factor in _ROOT_MULTIPLIERS:
        trial = guess * factor
        if trial <= 0.0:
            continue
        try:
            value = residual(trial)
        except (OutOfRangeError, ConvergenceError, InputError):
            continue
        if value <= 0.0:
            low, low_value = trial, value
        else:
            high, high_value = trial, value
        if low is not None and high is not None:
            break
    if low is None or high is None:
        raise OutOfRangeError(
            "m_c",
            guess,
            "存在使出口达到目标状态的单回路流量",
            "设计求根",
        )
    if low_value == 0.0:
        return low
    if high_value == 0.0:
        return high
    lower, upper = (low, high) if low < high else (high, low)
    return float(brentq(residual, lower, upper, xtol=1e-6, rtol=1e-4))


def _target_exit_enthalpy(common, pressure):
    t_sat = saturation_temperature(common.refrigerant, pressure)
    if common.subcooling <= 1e-4:
        return liquid_enthalpy(common.refrigerant, t_sat)
    return enthalpy_pt(common.refrigerant, t_sat - common.subcooling, pressure)


def _rate_candidate(tube, common, v_face, gamma):
    from evapcond.models import RatingInput

    return rate(
        RatingInput(
            geometry=tube,
            refrigerant=common.refrigerant,
            m_ref=common.m_ref,
            T_in=common.T_k + common.superheat,
            air=common.air,
            aux=common.aux,
            T_sat_in=common.T_k,
            v_face=v_face,
            gamma=gamma,
            le_f=common.le_f,
        ),
        config=common.config,
    )


def _ordered(hits):
    return sorted(hits, key=lambda hit: (hit.area, hit.power, hit.tube.N_r, hit.tube.L))


def _seen(hits):
    return {_identity(hit.tube, hit.gamma, hit.v_face) for hit in hits}


def _identity(tube, gamma, v_face):
    return (
        round(tube.d_o, 8),
        round(tube.S_T, 8),
        round(tube.S_L, 8),
        tube.N_r,
        round(tube.L, 8),
        round(gamma, 8),
        round(v_face, 8),
    )


def _edge_notes(hit):
    notes = []
    row_note = row_edge_warning(hit.tube.N_r)
    if row_note is not None:
        notes.append(row_note)
    length_note = length_edge_warning(hit.tube.L)
    if length_note is not None:
        notes.append(length_note)
    return notes


def _refinement_groups(design, ordered, seen):
    groups = []
    count = 0
    for hit in ordered[:3]:
        row_values = set(range(max(4, hit.tube.N_r - 2), min(SPEC_ROW_LIMIT, hit.tube.N_r + 2) + 1))
        row_values.update(expanded_rows(hit.tube.N_r))
        length_values = set()
        for offset in (-1.0, 0.0, 1.0):
            length = hit.tube.L + offset
            if 0.5 - 1e-12 <= length <= 10.0 + 1e-12:
                length_values.add(length)
        length_values.update(expanded_lengths(hit.tube.L))
        rows = tuple(sorted(row for row in row_values if 4 <= row <= SPEC_ROW_LIMIT))
        for length in sorted(length_values):
            pending = []
            for n_r in rows:
                tube = replace(hit.tube, N_r=n_r, N_t=1, L=length)
                if _identity(tube, hit.gamma, hit.v_face) in seen:
                    continue
                pending.append(n_r)
                seen.add(_identity(tube, hit.gamma, hit.v_face))
            if not pending:
                continue
            if count + len(pending) > 200:
                pending = pending[: 200 - count]
            if not pending:
                return tuple(groups), count
            base = replace(hit.tube, N_r=pending[0], N_t=1, L=length)
            groups.append(_Group(base, tuple(pending), hit.gamma, hit.v_face))
            count += len(pending)
            if count >= 200:
                return tuple(groups), count
    return tuple(groups), count


def _relaxation_suggestions(design, config, workers):
    suggestions = []
    velocity = design.v_face_max + 0.1
    limit = 2.0 * design.v_face_max
    while velocity <= limit + 1e-9:
        if _has_hit(replace(design, v_face_max=velocity), config, workers):
            suggestions.append(f"将迎面风速上限提高至 {velocity:.1f} m/s 可获得可行解")
            break
        velocity += 0.1
    upper = max(int(row) for row in design.rows) + 2
    while upper <= 40:
        rows = tuple(sorted(set(int(row) for row in design.rows) | {upper}))
        if _has_hit(replace(design, rows=rows), config, workers):
            suggestions.append(f"将管排上限提高至 {upper} 可获得可行解")
            break
        upper += 2
    length = max(float(value) for value in design.lengths) + 1.0
    while length <= 10.0 + 1e-12:
        lengths = tuple(sorted(set(float(value) for value in design.lengths) | {length}))
        if _has_hit(replace(design, lengths=lengths), config, workers):
            suggestions.append(f"将管长上限提高至 {length:.0f} m 可获得可行解")
            break
        length += 1.0
    return tuple(suggestions)


def _has_hit(design, config, workers):
    common = _common(design, config)
    hits, _warnings = _run_groups(
        _coarse_groups(design), common, workers, None, None, 0, 0
    )
    return bool(hits)
