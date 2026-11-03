"""校核：输入二选一、进口焓、传质系数，以及一次完整求解。"""

import ast
import math
import threading
from pathlib import Path

import pytest

from evapcond.airside import dry_air_mass_flow
from evapcond.correlations.film_air import MIZUSHINA_NOTE
from evapcond.errors import (
    CancelledError,
    InputError,
    OutOfRangeError,
    UnconfirmedCorrelationError,
)
from evapcond.geometry.tube import UNSUPPORTED_SURFACE_MESSAGE, face_area
from evapcond.models import AuxInput, PlateGeometry, RatingInput, SolverConfig, TubeGeometry
from evapcond.properties.humid_air import humid_air_state
from evapcond.properties.refrigerant import (
    R404A_PSEUDOPURE_NOTE,
    saturation_pressure,
    saturation_temperature,
    vapor_enthalpy,
)
from evapcond.rating import (
    INLET_AIR_PROPERTY_NOTE,
    SATURATED_VAPOR_INLET_NOTE,
    SPRAY_WATER_PROPERTY_NOTE,
    mean_mass_transfer_coefficient,
    refrigerant_inlet_enthalpy,
    resolve_face_velocity,
    resolve_spray_density,
    run,
)

ROOT = Path(__file__).resolve().parents[1]


def _kelvin(t_c):
    return t_c + 273.15


def _tube():
    return TubeGeometry(
        surface_type="tube_plain",
        d_o=0.01905,
        wall_thickness=0.002,
        k_w=63.9,
        S_T=2.5 * 0.01905,
        S_L=2.0 * 0.01905,
        N_r=4,
        N_t=1,
        L=2.0,
    )


def _aux():
    return AuxInput(
        zeta_de=2.0,
        zeta_lv=1.0,
        zeta_st=0.5,
        p_noz=150000.0,
        H_lift=4.0,
        pipe_length=20.0,
        pipe_diameter=0.05,
        zeta_pipe=1.5,
        pipe_roughness=5.0e-5,
    )


def _air(t_db=32.0, t_wb=26.0):
    return humid_air_state(101325.0, T_db=_kelvin(t_db), T_wb=_kelvin(t_wb))


def _rating(**overrides):
    tube = _tube()
    t_sat = _kelvin(40.0)
    values = dict(
        geometry=tube,
        refrigerant="R134a",
        m_ref=0.04,
        T_in=t_sat,
        air=_air(),
        aux=_aux(),
        T_sat_in=t_sat,
        air_volume_flow=8.0 * face_area(tube),
        m_spray=0.05 * 2.0 * tube.N_t * tube.L,
    )
    values.update(overrides)
    return RatingInput(**values)


def test_rating_module_does_not_import_coolprop_or_pyside():
    tree = ast.parse((ROOT / "evapcond" / "rating.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        modules = []
        if isinstance(node, ast.Import):
            modules = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules = [node.module.split(".")[0]]
        assert "CoolProp" not in modules
        assert "PySide6" not in modules


def test_either_or_inputs_and_missing_fields():
    tube = _tube()
    assert resolve_face_velocity(tube, None, 2.5 * face_area(tube)) == pytest.approx(2.5)
    assert resolve_spray_density(tube, None, 0.2) == pytest.approx(0.05)
    with pytest.raises(InputError):
        resolve_face_velocity(tube, 2.5, 1.0)
    with pytest.raises(InputError):
        resolve_spray_density(tube, 0.05, 0.2)
    with pytest.raises(InputError) as missing:
        run(_rating(v_face=None, air_volume_flow=None, gamma=None, m_spray=None, p_in=None, T_sat_in=None))
    text = str(missing.value)
    assert "v_f 或风量" in text
    assert "Γ 或喷淋水量" in text
    assert "进口压力或进口饱和温度" in text
    with pytest.raises(InputError):
        run(_rating(v_face=2.5))
    with pytest.raises(InputError):
        run(_rating(m_ref=0.0))
    with pytest.raises(InputError):
        run(_rating(v_face=0.0, air_volume_flow=None))


def test_inlet_enthalpy_saturation_superheat_and_r744():
    t_sat = _kelvin(40.0)
    pressure = saturation_pressure("R134a", t_sat)
    p_back, enthalpy, saturated = refrigerant_inlet_enthalpy("R134a", t_sat, T_sat_in=t_sat)
    assert saturated is True
    assert p_back == pytest.approx(pressure)
    assert enthalpy == pytest.approx(vapor_enthalpy("R134a", t_sat))
    agreed, _, saturated_again = refrigerant_inlet_enthalpy(
        "R134a", t_sat, p_in=pressure, T_sat_in=saturation_temperature("R134a", pressure)
    )
    assert saturated_again is True
    assert agreed == pytest.approx(pressure)
    p_hot, h_hot, saturated_hot = refrigerant_inlet_enthalpy(
        "R134a", t_sat + 5.0, p_in=pressure
    )
    assert saturated_hot is False
    assert p_hot == pytest.approx(pressure)
    assert h_hot > enthalpy
    with pytest.raises(InputError):
        refrigerant_inlet_enthalpy("R134a", t_sat, p_in=pressure, T_sat_in=t_sat + 1.0)
    with pytest.raises(OutOfRangeError) as r744:
        refrigerant_inlet_enthalpy("R744", _kelvin(35.0), T_sat_in=_kelvin(35.0))
    assert "R744 在该冷凝温度下不适用蒸发式冷凝" in str(r744.value)


def test_unsupported_geometry_is_refused_before_iteration():
    low_fin = TubeGeometry(
        surface_type="tube_lowfin",
        d_o=0.01905,
        wall_thickness=0.002,
        k_w=63.9,
        S_T=0.0381,
        S_L=0.0381,
        N_r=4,
        N_t=1,
        L=2.0,
        fin_height=0.0015,
        fin_pitch=0.001,
        fin_thickness=0.0003,
    )
    with pytest.raises(UnconfirmedCorrelationError) as caught:
        run(_rating(geometry=low_fin))
    assert str(caught.value) == UNSUPPORTED_SURFACE_MESSAGE
    plate = PlateGeometry(
        plate_width=0.5,
        plate_height=1.2,
        plate_spacing=0.004,
        n_plates=40,
        corrugation_angle=math.radians(60),
        corrugation_pitch=0.008,
        corrugation_depth=0.002,
    )
    with pytest.raises(UnconfirmedCorrelationError):
        run(_rating(geometry=plate))


def test_cancel_stops_before_a_solution():
    event = threading.Event()
    event.set()
    with pytest.raises(CancelledError):
        run(_rating(), cancel_event=event, config=SolverConfig(n_cv_target=20))


def test_rating_matches_solver_balances_and_auxiliary_terms():
    rating = _rating()
    calls = []
    result = run(
        rating,
        config=SolverConfig(n_cv_target=20),
        progress_cb=lambda done, total, text: calls.append((done, total, text)),
    )
    assert calls
    assert calls[-1][0] >= 1
    assert "迭代" in calls[-1][2]
    assert abs(rating.m_ref * (result.h_ref_in - result.h_ref_out) - result.Q) < 1e-6 * result.Q
    shares = (
        result.resistances.share_ref
        + result.resistances.share_wall
        + result.resistances.share_out
    )
    assert abs(shares - 1.0) < 1e-9
    assert result.T_film_min <= result.T_film_max
    assert result.h_m == pytest.approx(
        mean_mass_transfer_coefficient(rating.geometry, result.segments, rating.air.p)
    )
    assert result.h_m > 0.0
    v_face = resolve_face_velocity(
        rating.geometry, rating.v_face, rating.air_volume_flow
    )
    m_dry = dry_air_mass_flow(rating.air, v_face, face_area(rating.geometry))
    assert result.auxiliary.air_volume_flow == pytest.approx(rating.air_volume_flow)
    assert result.auxiliary.spray_mass_flow == pytest.approx(rating.m_spray)
    assert result.auxiliary.m_evap == pytest.approx(m_dry * (result.w_air_out - rating.air.w))
    assert result.auxiliary.m_makeup == pytest.approx(
        result.auxiliary.m_evap + result.auxiliary.m_blowdown + result.auxiliary.m_drift
    )
    assert result.auxiliary.m_drift == pytest.approx(0.0001 * rating.m_spray)
    assert result.auxiliary.fan_power > 0.0
    assert result.auxiliary.pump_power > 0.0
    assert result.auxiliary.estimated_wet_correction is True
    assert result.segments
    text = "\n".join(result.diagnostics)
    assert MIZUSHINA_NOTE in text
    assert INLET_AIR_PROPERTY_NOTE in text
    assert SPRAY_WATER_PROPERTY_NOTE in text
    assert SATURATED_VAPOR_INLET_NOTE in text
    assert R404A_PSEUDOPURE_NOTE not in text
    assert result.region_out in ("subcooled", "two_phase", "superheated")
    assert (result.x_out is not None) or (result.subcooling is not None) or (
        result.superheat is not None
    )


def test_r404a_diagnostics_include_the_pseudo_pure_sentence():
    t_sat = _kelvin(40.0)
    result = run(
        _rating(
            refrigerant="R404A",
            T_in=t_sat,
            T_sat_in=None,
            p_in=saturation_pressure("R404A", t_sat),
            v_face=8.0,
            air_volume_flow=None,
        ),
        config=SolverConfig(n_cv_target=20),
    )
    assert R404A_PSEUDOPURE_NOTE in result.diagnostics
    assert result.Q > 0.0
