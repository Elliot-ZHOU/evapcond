"""分段求解器：收敛、守恒、热阻占比，以及 n_L 加倍后的换热量。"""

import ast
import threading
from pathlib import Path

import pytest

from evapcond.errors import CancelledError, InputError, OutOfRangeError
from evapcond.models import SolverConfig, TubeGeometry
from evapcond.properties.humid_air import humid_air_state
from evapcond.properties.refrigerant import saturation_pressure, vapor_enthalpy
from evapcond.properties.water import latent_heat, specific_heat, vapor_enthalpy as vapor_water
from evapcond.solver import segments_per_row, solve, temperature_at_saturated_enthalpy

ROOT = Path(__file__).resolve().parents[1]


def _kelvin(t_c):
    return t_c + 273.15


def _tube(n_r=4):
    return TubeGeometry(
        surface_type="tube_plain",
        d_o=0.01905,
        wall_thickness=0.002,
        k_w=63.9,
        S_T=0.0381,
        S_L=0.0381,
        N_r=n_r,
        N_t=1,
        L=2.0,
    )


def _case(t_k, t_db, t_wb, m_dot, v_face, gamma):
    tube = _tube()
    pressure = saturation_pressure("R134a", _kelvin(t_k))
    enthalpy = vapor_enthalpy("R134a", _kelvin(t_k))
    air = humid_air_state(101325.0, T_db=_kelvin(t_db), T_wb=_kelvin(t_wb))
    return tube, pressure, enthalpy, air, m_dot, v_face, gamma


CASES = (
    (40.0, 32.0, 26.0, 0.04, 8.0, 0.05),
    (38.0, 30.0, 24.0, 0.035, 10.0, 0.045),
    (42.0, 34.0, 27.0, 0.045, 12.0, 0.055),
)


def test_solver_does_not_import_coolprop_or_gui():
    tree = ast.parse((ROOT / "evapcond" / "solver.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        modules = []
        if isinstance(node, ast.Import):
            modules = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules = [node.module.split(".")[0]]
        assert "CoolProp" not in modules
        assert "PySide6" not in modules


def test_segment_count_and_rejected_inputs():
    assert segments_per_row(4, 40) == 10
    assert segments_per_row(6, 40) == 7
    with pytest.raises(OutOfRangeError):
        SolverConfig(n_cv_target=19)
    tube, pressure, enthalpy, air, m_dot, v_face, gamma = _case(*CASES[0])
    with pytest.raises(InputError):
        solve(tube, "R134a", 0.0, pressure, enthalpy, air, v_face, gamma)
    with pytest.raises(InputError):
        solve(tube, "R134a", m_dot, pressure, enthalpy, air, 0.0, gamma)
    lowfin = TubeGeometry(
        surface_type="tube_lowfin",
        d_o=0.01905,
        wall_thickness=0.002,
        k_w=63.9,
        S_T=0.0381,
        S_L=0.0381,
        N_r=4,
        N_t=1,
        L=2.0,
        fin_height=0.001,
        fin_pitch=0.002,
        fin_thickness=0.0002,
    )
    from evapcond.errors import UnconfirmedCorrelationError

    with pytest.raises(UnconfirmedCorrelationError):
        solve(lowfin, "R134a", m_dot, pressure, enthalpy, air, v_face, gamma)


def test_cancel_before_iteration():
    tube, pressure, enthalpy, air, m_dot, v_face, gamma = _case(*CASES[0])
    event = threading.Event()
    event.set()
    with pytest.raises(CancelledError):
        solve(
            tube,
            "R134a",
            m_dot,
            pressure,
            enthalpy,
            air,
            v_face,
            gamma,
            cancel_event=event,
        )


def _solve_case(values, n_cv_target=40):
    tube, pressure, enthalpy, air, m_dot, v_face, gamma = _case(*values)
    result = solve(
        tube,
        "R134a",
        m_dot,
        pressure,
        enthalpy,
        air,
        v_face,
        gamma,
        config=SolverConfig(n_cv_target=n_cv_target),
    )
    return tube, pressure, enthalpy, air, m_dot, result


def test_converged_solution_conserves_energy_and_water():
    tube, pressure, enthalpy, air, m_dot, result = _solve_case(CASES[0])
    assert result.n_L == 10
    assert result.convergence.iterations < 500
    assert result.convergence.heat_relative < 1e-4
    assert result.convergence.film_temperature < 1e-3
    assert result.convergence.air_enthalpy < 10.0
    assert result.energy_residual < 1e-6 * result.Q
    assert result.water_mass_residual < 1e-9
    assert abs(m_dot * (enthalpy - result.h_ref_out) - result.Q) < 1e-6 * result.Q

    evaporated = 0.0
    air_gain = 0.0
    for segment in result.segments:
        h_fg = latent_heat(segment.T_w)
        i_g = vapor_water(segment.T_w)
        dm = segment.dQ_l / h_fg
        evaporated += dm
        air_gain += segment.dQ_s + dm * i_g
    assert abs(result.m_dry * (result.air_out.h - air.h) - air_gain) < 1e-6 * result.Q
    assert abs(result.m_dry * (result.air_out.w - air.w) - evaporated) < 1e-9

    by_place = {(segment.row, segment.seg): segment for segment in result.segments}
    area = 3.141592653589793 * tube.d_o * tube.L / result.n_L
    share_num = [0.0, 0.0, 0.0]
    share_den = 0.0
    k_den = 0.0
    for segment in result.segments:
        drops = (
            segment.dQ_ref * segment.R_ref,
            segment.dQ_ref * segment.R_wall,
            segment.dQ_ref * segment.R_out,
        )
        for index, drop in enumerate(drops):
            share_num[index] += drop * segment.dQ_ref
            share_den += drop * segment.dQ_ref
        t_star = temperature_at_saturated_enthalpy(segment.i_a, air.p)
        k_den += area * (segment.T_ref - t_star)
    assert abs(share_num[0] / share_den - result.resistances.share_ref) < 1e-12
    shares = (
        result.resistances.share_ref
        + result.resistances.share_wall
        + result.resistances.share_out
    )
    assert abs(shares - 1.0) < 1e-9
    assert result.resistances.K == pytest.approx(result.Q / k_den)

    for seg in range(1, result.n_L + 1):
        assert by_place[(tube.N_r, seg)].i_a == pytest.approx(air.h)
    assert result.segments[0].row == 1 and result.segments[0].seg == 1
    assert result.segments[result.n_L].row == 2 and result.segments[result.n_L].seg == result.n_L
    assert result.segments[result.n_L - 1].h_ref > result.segments[result.n_L].h_ref

    total = 0.0
    for seg in range(1, result.n_L + 1):
        temperature_in = result.T_spray
        for row in range(1, tube.N_r + 1):
            segment = by_place[(row, seg)]
            cp = specific_heat(segment.T_w)
            net = segment.dQ_ref - segment.dQ_s - segment.dQ_l
            temperature_out = temperature_in + net / (segment.m_w * cp)
            total += abs(segment.m_w * cp * (segment.T_w - temperature_out))
            temperature_in = segment.T_w
    assert total < 1e-6 * result.Q
    assert any("Re_GT" in warning for warning in result.warnings)


def test_doubling_n_l_changes_heat_by_less_than_half_percent():
    for values in CASES:
        _, _, _, _, _, coarse = _solve_case(values, 40)
        _, _, _, _, _, fine = _solve_case(values, 80)
        assert fine.n_L == 2 * coarse.n_L
        assert abs(fine.Q - coarse.Q) / abs(coarse.Q) < 0.005
