"""分段迭代求解器。空气自下而上，喷淋水自上而下，制冷剂蛇形自上而下。

一个回路算完后，换热量、蒸发量和空气流量乘以并联回路数 N_t。
湿空气焓用 HAPropsSI 的绝对值。汽相焓 i_g 只作为增量加到这个焓上，
不与 HEOS 的绝对焓相加。二者参考态不同。
"""

import math
from dataclasses import dataclass

from scipy.optimize import brentq

from evapcond.airside import (
    advance_moist_air,
    air_side_rates,
    dry_air_mass_flow,
    film_resistance,
    gamma_m_from_gamma,
    saturation_humidity,
)
from evapcond.correlations.film_air import (
    air_convection_coefficient,
    bosnjakovic_lewis_factor,
    film_convection_coefficient,
)
from evapcond.errors import (
    CancelledError,
    ConvergenceError,
    InputError,
    OutOfRangeError,
)
from evapcond.geometry.tube import require_supported_surface, segment_outside_area
from evapcond.models import (
    ConvergenceInfo,
    ResistanceSummary,
    SegmentState,
    SolverConfig,
    TubeGeometry,
)
from evapcond.properties.humid_air import humid_air_state
from evapcond.properties.water import latent_heat, specific_heat, vapor_enthalpy
from evapcond.refside import evaluate_refrigerant_segment

HEAT_RELATIVE_TOLERANCE = 1e-4
FILM_TEMPERATURE_TOLERANCE = 1e-3
AIR_ENTHALPY_TOLERANCE = 10.0
ENERGY_RELATIVE_TOLERANCE = 1e-6
WATER_MASS_TOLERANCE = 1e-9
_T_AIR_MIN = 5.0 + 273.15
_T_AIR_MAX = 50.0 + 273.15


@dataclass(frozen=True)
class SolverResult:
    """一个管束的求解结果。段状态按制冷剂流动顺序排列，数值是单回路的。"""

    segments: tuple
    Q: float
    T_spray: float
    air_out: object
    m_dry: float
    m_evap: float
    m_water_in: float
    m_water_out: float
    h_ref_in: float
    h_ref_out: float
    p_out: float
    resistances: ResistanceSummary
    convergence: ConvergenceInfo
    warnings: tuple
    correlations: tuple
    n_L: int
    energy_residual: float
    water_mass_residual: float


def segments_per_row(n_r, n_cv_target):
    """n_L = ceil(N_cv_target / N_r)。"""
    if type(n_r) is not int or n_r < 1:
        raise InputError("N_r 必须是正整数")
    if type(n_cv_target) is not int or n_cv_target < 20:
        raise OutOfRangeError(
            "N_cv_target",
            n_cv_target,
            ">= 20",
            "规格：控制容积不得少于 20",
        )
    return math.ceil(n_cv_target / n_r)


def solve(
    tube,
    refrigerant,
    m_dot,
    p_in,
    h_in,
    air_in,
    v_face,
    gamma,
    config=None,
    progress_cb=None,
    cancel_event=None,
    le_f=None,
):
    """求解整台管束。m_dot 是全部回路的制冷剂流量，kg/s。"""
    if config is None:
        config = SolverConfig()
    if not isinstance(config, SolverConfig):
        raise InputError("config 必须是 SolverConfig")
    if not isinstance(tube, TubeGeometry):
        raise InputError("需要 TubeGeometry")
    require_supported_surface(tube.surface_type)
    if not math.isfinite(m_dot) or m_dot <= 0.0:
        raise InputError("制冷剂流量必须大于 0")
    if not math.isfinite(v_face) or v_face <= 0.0:
        raise InputError("v_f 必须大于 0")
    if not math.isfinite(gamma) or gamma <= 0.0:
        raise InputError("Γ 必须大于 0")
    n_l = segments_per_row(tube.N_r, config.n_cv_target)
    dL = tube.L / n_l
    area = segment_outside_area(tube, dL)
    m_circuit = m_dot / tube.N_t
    m_dry_segment = dry_air_mass_flow(air_in, v_face, tube.S_T * dL)
    spray_segment = gamma * 2.0 * dL
    path = _flow_path(tube.N_r, n_l)
    t_wall = _filled(tube.N_r, n_l, air_in.T_wb)
    water_flow = _filled(tube.N_r, n_l, spray_segment)
    spray = air_in.T_wb
    previous_enthalpy = None
    previous_heat = None
    cells = None
    heat_relative = math.inf
    film_change = math.inf
    enthalpy_change = math.inf
    for iteration in range(1, config.max_iterations + 1):
        if cancel_event is not None and cancel_event.is_set():
            raise CancelledError("已取消")
        cells = _evaluate_field(
            tube,
            refrigerant,
            m_circuit,
            p_in,
            h_in,
            air_in,
            m_dry_segment,
            area,
            dL,
            path,
            t_wall,
            water_flow,
            le_f,
        )
        proposed = _implicit_water_update(
            tube, cells, spray, spray_segment, area, dL, le_f
        )
        heat = _circuit_heat(cells)
        heat_relative = _relative_heat(heat, previous_heat)
        film_change = _max_temperature_change(t_wall, proposed.temperature, spray, proposed.spray)
        enthalpy_change = _max_enthalpy_change(cells, previous_enthalpy)
        imbalance = _stored_energy_imbalance(cells, t_wall, water_flow, spray)
        if progress_cb is not None:
            progress_cb(
                iteration,
                config.max_iterations,
                (
                    f"迭代 {iteration}，换热量相对变化 {heat_relative:.3e}，"
                    f"水膜温度变化 {film_change:.3e} K，"
                    f"空气焓变化 {enthalpy_change / 1000.0:.3e} kJ/kg"
                ),
            )
        converged = (
            previous_heat is not None
            and heat_relative < HEAT_RELATIVE_TOLERANCE
            and film_change < FILM_TEMPERATURE_TOLERANCE
            and enthalpy_change < AIR_ENTHALPY_TOLERANCE
            and imbalance < ENERGY_RELATIVE_TOLERANCE * max(abs(heat), 1e-12)
        )
        if converged:
            return _assemble(
                tube,
                cells,
                t_wall,
                water_flow,
                spray,
                air_in,
                m_dry_segment,
                spray_segment,
                h_in,
                area,
                n_l,
                ConvergenceInfo(
                    iterations=iteration,
                    heat_relative=heat_relative,
                    film_temperature=film_change,
                    air_enthalpy=enthalpy_change,
                ),
                imbalance,
            )
        t_wall = _relax_field(t_wall, proposed.temperature, config.relaxation)
        water_flow = _relax_field(water_flow, proposed.flow, config.relaxation)
        spray = spray + config.relaxation * (proposed.spray - spray)
        previous_enthalpy = _enthalpy_field(cells)
        previous_heat = heat
    raise ConvergenceError(
        (
            "求解未在迭代上限内收敛："
            f"换热量相对变化 {heat_relative:.3e}，"
            f"水膜温度变化 {film_change:.3e} K，"
            f"空气焓变化 {enthalpy_change / 1000.0:.3e} kJ/kg"
        ),
        (heat_relative, film_change, enthalpy_change / 1000.0),
    )


def _flow_path(n_r, n_l):
    path = []
    for row in range(n_r):
        order = range(n_l) if row % 2 == 0 else range(n_l - 1, -1, -1)
        for seg in order:
            path.append((row, seg))
    return tuple(path)


def _filled(n_r, n_l, value):
    return [[value for _ in range(n_l)] for _ in range(n_r)]


@dataclass(frozen=True)
class _AirCell:
    inlet: object
    outlet: object
    dQ_s: float
    dm_ev: float
    dQ_l: float
    R_film: float
    i_g: float
    correlations: tuple


@dataclass(frozen=True)
class _Field:
    air: list
    refrigerant: list
    warnings: tuple
    correlations: tuple


@dataclass(frozen=True)
class _WaterUpdate:
    temperature: list
    flow: list
    spray: float
    outlet_temperature: tuple
    outlet_flow: tuple


def _evaluate_field(
    tube,
    refrigerant,
    m_circuit,
    p_in,
    h_in,
    air_in,
    m_dry,
    area,
    dL,
    path,
    t_wall,
    water_flow,
    le_f,
):
    n_r = tube.N_r
    n_l = len(t_wall[0])
    air = [[None for _ in range(n_l)] for _ in range(n_r)]
    warnings = []
    correlations = []
    for seg in range(n_l):
        state = air_in
        for row in range(n_r - 1, -1, -1):
            cell, cell_warnings, cell_correlations = _air_cell(
                tube, state, t_wall[row][seg], water_flow[row][seg], area, dL, m_dry, le_f
            )
            air[row][seg] = cell
            state = cell.outlet
            warnings.extend(cell_warnings)
            correlations.extend(cell_correlations)
    refrigerant_cells = [[None for _ in range(n_l)] for _ in range(n_r)]
    pressure = p_in
    enthalpy = h_in
    for row, seg in path:
        segment = evaluate_refrigerant_segment(
            refrigerant,
            tube.d_i,
            tube.d_o,
            tube.k_w,
            dL,
            m_circuit,
            pressure,
            enthalpy,
            t_wall[row][seg],
            air[row][seg].R_film,
        )
        refrigerant_cells[row][seg] = segment
        pressure = segment.state_out.p
        enthalpy = segment.state_out.h
        warnings.extend(segment.warnings)
        correlations.extend(segment.correlations)
    return _Field(
        air=air,
        refrigerant=refrigerant_cells,
        warnings=tuple(_unique(warnings)),
        correlations=tuple(_unique_records(correlations)),
    )


def _air_cell(tube, inlet, t_film, m_water, area, dL, m_dry, le_f):
    dQ_s, dm_ev, dQ_l, h_w, i_g, correlations = _air_rates(
        tube, inlet, t_film, m_water, area, dL, le_f
    )
    outlet = advance_moist_air(inlet, m_dry, dQ_s, dm_ev, i_g)
    cell = _AirCell(
        inlet=inlet,
        outlet=outlet,
        dQ_s=dQ_s,
        dm_ev=dm_ev,
        dQ_l=dQ_l,
        R_film=film_resistance(h_w, area),
        i_g=i_g,
        correlations=correlations,
    )
    return cell, (), cell.correlations


def _air_rates(tube, inlet, t_film, m_water, area, dL, le_f):
    if m_water <= 0.0 or not math.isfinite(m_water):
        raise OutOfRangeError("m_w", m_water, "> 0 kg/s", "喷淋水流量")
    gamma = m_water / (2.0 * dL)
    gamma_m = gamma_m_from_gamma(gamma, tube.d_o, tube.S_T)
    h_c, hc_record = air_convection_coefficient(gamma_m, tube.d_o)
    h_w, hw_record = film_convection_coefficient(gamma_m, tube.d_o)
    w_s = saturation_humidity(t_film, inlet.p)
    lewis, lewis_record = bosnjakovic_lewis_factor(w_s, inlet.w, le_f=le_f)
    h_m = h_c / (inlet.cp * lewis)
    h_fg = latent_heat(t_film)
    i_g = vapor_enthalpy(t_film)
    dQ_s, dm_ev, dQ_l = air_side_rates(
        h_c, h_m, area, t_film, inlet.T_db, w_s, inlet.w, h_fg
    )
    return dQ_s, dm_ev, dQ_l, h_w, i_g, (hc_record, hw_record, lewis_record)


def _implicit_water_update(tube, field, spray, spray_segment, area, dL, le_f):
    """水膜温度取能量平衡的出口温度，并在该温度上计算热流。"""
    n_r = len(field.air)
    n_l = len(field.air[0])
    temperature = _filled(n_r, n_l, 0.0)
    flow = _filled(n_r, n_l, 0.0)
    outlet_temperature = []
    outlet_flow = []
    for seg in range(n_l):
        temperature_in = spray
        flow_in = spray_segment
        for row in range(n_r):
            refrigerant = field.refrigerant[row][seg]
            resistance = refrigerant.R_ref + refrigerant.R_wall + refrigerant.R_film
            film, evaporated = _solve_film_temperature(
                tube,
                field.air[row][seg].inlet,
                temperature_in,
                flow_in,
                area,
                dL,
                le_f,
                refrigerant.state_in.T,
                resistance,
            )
            flow_out = flow_in - evaporated
            if flow_out <= 0.0:
                raise OutOfRangeError("m_w", flow_out, "> 0 kg/s", "喷淋水在底排前蒸发完")
            temperature[row][seg] = film
            flow[row][seg] = flow_in
            temperature_in = film
            flow_in = flow_out
        outlet_temperature.append(temperature_in)
        outlet_flow.append(flow_in)
    mass = sum(outlet_flow)
    mixed = sum(
        value * flow_value
        for value, flow_value in zip(outlet_temperature, outlet_flow)
    ) / mass
    return _WaterUpdate(
        temperature=temperature,
        flow=flow,
        spray=mixed,
        outlet_temperature=tuple(outlet_temperature),
        outlet_flow=tuple(outlet_flow),
    )


def _solve_film_temperature(
    tube, inlet_air, temperature_in, flow_in, area, dL, le_f, t_ref, resistance
):
    """求解 T_w = T_in + (dQ_ref - dQ_s - dQ_l) / (m c_p)。返回水膜温度和蒸发量。"""
    guess = temperature_in
    evaporated = 0.0
    for _ in range(8):
        net, evaporated, slope = _net_and_slope(
            tube, inlet_air, guess, flow_in, area, dL, le_f, t_ref, resistance
        )
        cp = specific_heat(guess)
        mismatch = guess - temperature_in - net / (flow_in * cp)
        derivative = 1.0 - slope / (flow_in * cp)
        if derivative == 0.0 or not math.isfinite(derivative):
            raise ConvergenceError(
                "水膜温度的局部能量平衡没有可用导数",
                (math.inf, math.inf, math.inf),
            )
        step = mismatch / derivative
        guess -= step
        if not math.isfinite(guess):
            raise OutOfRangeError("T_w", guess, "5 °C ～ 50 °C", "水膜能量")
        if abs(step) < 1e-8:
            return guess, evaporated
    net, evaporated, _ = _net_and_slope(
        tube, inlet_air, guess, flow_in, area, dL, le_f, t_ref, resistance
    )
    return guess, evaporated


def _net_and_slope(
    tube, inlet_air, temperature, flow_in, area, dL, le_f, t_ref, resistance
):
    net, evaporated = _film_net(
        tube, inlet_air, temperature, flow_in, area, dL, le_f, t_ref, resistance
    )
    step = 1e-3
    net_up, _ = _film_net(
        tube, inlet_air, temperature + step, flow_in, area, dL, le_f, t_ref, resistance
    )
    return net, evaporated, (net_up - net) / step


def _film_net(
    tube, inlet_air, temperature, flow_in, area, dL, le_f, t_ref, resistance
):
    dQ_s, dm_ev, dQ_l = _air_rates(
        tube, inlet_air, temperature, flow_in, area, dL, le_f
    )[:3]
    dQ_ref = (t_ref - temperature) / resistance
    return dQ_ref - dQ_s - dQ_l, dm_ev


def _stored_energy_imbalance(field, t_wall, water_flow, spray):
    """已保存的热流和水膜温度对能量方程的偏差，W。"""
    total = 0.0
    n_r = len(t_wall)
    n_l = len(t_wall[0])
    outlet_temperature = []
    outlet_flow = []
    for seg in range(n_l):
        temperature_in = spray
        for row in range(n_r):
            air = field.air[row][seg]
            refrigerant = field.refrigerant[row][seg]
            cp = specific_heat(t_wall[row][seg])
            net = refrigerant.dQ_ref - air.dQ_s - air.dQ_l
            temperature_out = temperature_in + net / (water_flow[row][seg] * cp)
            total += abs(water_flow[row][seg] * cp * (t_wall[row][seg] - temperature_out))
            temperature_in = t_wall[row][seg]
        outlet_temperature.append(temperature_in)
        outlet_flow.append(water_flow[n_r - 1][seg] - field.air[n_r - 1][seg].dm_ev)
    mass = sum(outlet_flow)
    if mass > 0.0:
        mixed = sum(
            value * flow for value, flow in zip(outlet_temperature, outlet_flow)
        ) / mass
        total += abs(mass * specific_heat(spray) * (mixed - spray))
    return total


def _assemble(
    tube,
    field,
    t_wall,
    water_flow,
    spray,
    air_in,
    m_dry_segment,
    spray_segment,
    h_in,
    area,
    n_l,
    convergence,
    imbalance,
):
    n_r = tube.N_r
    n_t = tube.N_t
    segments = []
    for row, seg in _flow_path(n_r, n_l):
        air = field.air[row][seg]
        refrigerant = field.refrigerant[row][seg]
        t_star = temperature_at_saturated_enthalpy(air.inlet.h, air.inlet.p)
        t_wall_outer = refrigerant.state_in.T - refrigerant.dQ_ref * (
            refrigerant.R_ref + refrigerant.R_wall
        )
        if refrigerant.dQ_ref == 0.0:
            raise OutOfRangeError("dQ_ref", 0.0, "非零", "外侧等效热阻")
        r_out = (t_wall_outer - t_star) / refrigerant.dQ_ref
        quality = refrigerant.state_in.x
        segments.append(
            SegmentState(
                row=row + 1,
                seg=seg + 1,
                region=refrigerant.state_in.region,
                T_ref=refrigerant.state_in.T,
                p=refrigerant.state_in.p,
                x=quality,
                h_ref=refrigerant.state_in.h,
                T_w=t_wall[row][seg],
                m_w=water_flow[row][seg],
                T_a=air.inlet.T_db,
                w_a=air.inlet.w,
                i_a=air.inlet.h,
                dQ_ref=refrigerant.dQ_ref,
                dQ_s=air.dQ_s,
                dQ_l=air.dQ_l,
                R_ref=refrigerant.R_ref,
                R_wall=refrigerant.R_wall,
                R_out=r_out,
            )
        )
    last = field.refrigerant[_flow_path(n_r, n_l)[-1][0]][_flow_path(n_r, n_l)[-1][1]]
    h_mix = sum(field.air[0][seg].outlet.h for seg in range(n_l)) / n_l
    w_mix = sum(field.air[0][seg].outlet.w for seg in range(n_l)) / n_l
    air_out = humid_air_state(air_in.p, w=w_mix, h=h_mix)
    circuit_heat = _circuit_heat(field)
    m_evap_circuit = sum(field.air[row][seg].dm_ev for row in range(n_r) for seg in range(n_l))
    m_dry = m_dry_segment * n_l * n_t
    water_mass_residual = abs(m_dry * (air_out.w - air_in.w) - m_evap_circuit * n_t)
    return SolverResult(
        segments=tuple(segments),
        Q=circuit_heat * n_t,
        T_spray=spray,
        air_out=air_out,
        m_dry=m_dry,
        m_evap=m_evap_circuit * n_t,
        m_water_in=spray_segment * n_l * n_t,
        m_water_out=sum(
            water_flow[n_r - 1][seg] - field.air[n_r - 1][seg].dm_ev for seg in range(n_l)
        )
        * n_t,
        h_ref_in=h_in,
        h_ref_out=last.state_out.h,
        p_out=last.state_out.p,
        resistances=_resistance_summary(segments, area, circuit_heat),
        convergence=convergence,
        warnings=field.warnings,
        correlations=field.correlations,
        n_L=n_l,
        energy_residual=imbalance * n_t,
        water_mass_residual=water_mass_residual,
    )


def temperature_at_saturated_enthalpy(enthalpy, pressure):
    """饱和空气焓等于 enthalpy 时的温度，K。"""
    h_low = humid_air_state(pressure, T_db=_T_AIR_MIN, rh=1.0).h
    h_high = humid_air_state(pressure, T_db=_T_AIR_MAX, rh=1.0).h
    if enthalpy < h_low or enthalpy > h_high:
        raise OutOfRangeError(
            "i_a",
            enthalpy,
            f"[{h_low}, {h_high}] J/kg",
            "饱和空气焓对应的干球温度",
        )

    def gap(temperature):
        return humid_air_state(pressure, T_db=temperature, rh=1.0).h - enthalpy

    if abs(gap(_T_AIR_MIN)) <= 1e-6:
        return _T_AIR_MIN
    if abs(gap(_T_AIR_MAX)) <= 1e-6:
        return _T_AIR_MAX
    return brentq(gap, _T_AIR_MIN, _T_AIR_MAX, xtol=1e-8, rtol=1e-10)


def _resistance_summary(segments, area, circuit_heat):
    numerator = [0.0, 0.0, 0.0]
    denominator = 0.0
    weighted_r = [0.0, 0.0, 0.0]
    heat_sum = 0.0
    k_denominator = 0.0
    for segment in segments:
        d_ref = segment.dQ_ref * segment.R_ref
        d_wall = segment.dQ_ref * segment.R_wall
        d_out = segment.dQ_ref * segment.R_out
        q = segment.dQ_ref
        numerator[0] += d_ref * q
        numerator[1] += d_wall * q
        numerator[2] += d_out * q
        denominator += (d_ref + d_wall + d_out) * q
        weighted_r[0] += segment.R_ref * q
        weighted_r[1] += segment.R_wall * q
        weighted_r[2] += segment.R_out * q
        heat_sum += q
        k_denominator += area * (d_ref + d_wall + d_out)
    if denominator == 0.0 or heat_sum == 0.0 or k_denominator == 0.0:
        raise OutOfRangeError("Q", circuit_heat, "非零", "热阻占比")
    return ResistanceSummary(
        share_ref=numerator[0] / denominator,
        share_wall=numerator[1] / denominator,
        share_out=numerator[2] / denominator,
        K=circuit_heat / k_denominator,
        R_ref=weighted_r[0] / heat_sum,
        R_wall=weighted_r[1] / heat_sum,
        R_out=weighted_r[2] / heat_sum,
    )


def _circuit_heat(field):
    return sum(
        segment.dQ_ref
        for row in field.refrigerant
        for segment in row
    )


def _relative_heat(heat, previous):
    if previous is None:
        return math.inf
    scale = max(abs(heat), abs(previous), 1e-12)
    return abs(heat - previous) / scale


def _max_temperature_change(t_wall, proposed, spray, proposed_spray):
    gap = abs(proposed_spray - spray)
    for row, values in enumerate(t_wall):
        for seg, value in enumerate(values):
            gap = max(gap, abs(proposed[row][seg] - value))
    return gap


def _enthalpy_field(field):
    return [
        [cell.inlet.h for cell in row]
        for row in field.air
    ]


def _max_enthalpy_change(field, previous):
    if previous is None:
        return math.inf
    gap = 0.0
    for row, cells in enumerate(field.air):
        for seg, cell in enumerate(cells):
            gap = max(gap, abs(cell.inlet.h - previous[row][seg]))
    return gap


def _relax_field(current, proposed, factor):
    return [
        [
            value + factor * (proposed[row][seg] - value)
            for seg, value in enumerate(values)
        ]
        for row, values in enumerate(current)
    ]


def _unique(items):
    seen = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen


def _unique_records(records):
    seen = []
    names = set()
    for record in records:
        if record.name in names:
            continue
        names.add(record.name)
        seen.append(record)
    return seen
