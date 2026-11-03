"""辅机：干管束欧拉数、湿修正、Colebrook、风机水泵与补水。"""

import ast
import math
from pathlib import Path

import pytest
from scipy.optimize import brentq

from evapcond.auxiliary import DRIFT_ENGINEERING_NOTE, evaluate_auxiliary
from evapcond.correlations.bundle_pressure import (
    EQUILATERAL_K1_NOTE,
    EULER_ROWS,
    GAMMA_REF,
    WET_ESTIMATE_NOTE,
    ZUKAUSKAS_BASIS_NOTE,
    dry_bundle_pressure_drop,
    euler_number,
    row_correction,
    wet_pressure_drop,
)
from evapcond.correlations.pipe_friction import COLEBROOK_TOLERANCE, darcy_friction_factor
from evapcond.correlations.pressure_drop import STANDARD_GRAVITY
from evapcond.errors import InputError, OutOfRangeError, UnconfirmedCorrelationError
from evapcond.geometry.tube import UNSUPPORTED_SURFACE_MESSAGE, face_area
from evapcond.models import AuxInput, PlateGeometry, TubeGeometry

ROOT = Path(__file__).resolve().parents[1]


def _tube(**overrides):
    d_o = 0.01905
    values = dict(
        surface_type="tube_plain",
        d_o=d_o,
        wall_thickness=0.002,
        k_w=63.9,
        S_T=2.0 * d_o,
        S_L=1.5 * d_o,
        N_r=8,
        N_t=10,
        L=4.0,
    )
    values.update(overrides)
    return TubeGeometry(**values)


def _aux(**overrides):
    values = dict(
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
    values.update(overrides)
    return AuxInput(**values)


def _series(row, reynolds):
    q, r, s, t, u = row[4:]
    inverse = 1.0 / reynolds
    return q + inverse * (r + inverse * (s + inverse * (t + inverse * u)))


def _row(spacing, lower):
    return next(item for item in EULER_ROWS if item[0] == spacing and item[1] == lower)


def test_auxiliary_modules_do_not_import_coolprop_or_pyside():
    paths = [
        ROOT / "evapcond" / "auxiliary.py",
        ROOT / "evapcond" / "correlations" / "bundle_pressure.py",
        ROOT / "evapcond" / "correlations" / "pipe_friction.py",
    ]
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module.split(".")[0]]
            assert "CoolProp" not in modules
            assert "PySide6" not in modules


def test_disputed_euler_coefficients_follow_the_figure():
    assert _row(1.25, 1.0e3)[8] == -0.599e13
    assert _row(2.0, 7.0)[7] == -0.582e3
    assert _row(2.5, 1.0e2)[8] == 0.862e8
    assert _row(1.25, 1.0e3)[8] != -0.559e13
    assert _row(2.0, 7.0)[7] != -0.585e7
    assert _row(2.5, 1.0e2)[8] != 0.862e2
    assert len(EULER_ROWS) == 9


def test_euler_series_and_shared_boundary():
    eu, record = euler_number(2.5, 1.0e3)
    assert eu == pytest.approx(_series(_row(2.5, 1.0e2), 1.0e3))
    assert eu > 0.0
    assert ("k_1", 1.0) in record.parameters
    high = euler_number(2.0, 100.0)[0]
    assert high == pytest.approx(_series(_row(2.0, 1.0e2), 100.0))
    assert high != pytest.approx(_series(_row(2.0, 7.0), 100.0))
    low = euler_number(2.0, 99.0)[0]
    assert low == pytest.approx(_series(_row(2.0, 7.0), 99.0))
    top = euler_number(1.25, 2.0e6)[0]
    assert top == pytest.approx(_series(_row(1.25, 1.0e3), 2.0e6))


def test_euler_rejects_spacing_reynolds_and_non_positive_value():
    with pytest.raises(OutOfRangeError) as spacing:
        euler_number(1.8, 1.0e3)
    assert spacing.value.param == "S_T/d_o"
    with pytest.raises(OutOfRangeError) as low_re:
        euler_number(2.0, 6.999)
    assert low_re.value.param == "Re_max"
    with pytest.raises(OutOfRangeError) as high_re:
        euler_number(2.0, 2.0e6 + 1.0)
    assert high_re.value.param == "Re_max"
    with pytest.raises(OutOfRangeError) as negative:
        euler_number(2.0, 1.0e4)
    assert negative.value.param == "Eu"


def test_row_correction_changes_only_below_ten_rows():
    assert row_correction(4)[0] == pytest.approx(1.0 - 0.45 * math.exp(-4.0 / 3.0))
    assert row_correction(9)[0] == pytest.approx(1.0 - 0.45 * math.exp(-3.0))
    assert row_correction(10)[0] == 1.0
    assert row_correction(28)[0] == 1.0
    with pytest.raises(InputError):
        row_correction(0)


def test_dry_and_wet_pressure_drop():
    rho = 1.2
    v_max = 4.0
    n_r = 8
    euler = 0.4
    c2 = row_correction(n_r)[0]
    dry = dry_bundle_pressure_drop(rho, v_max, n_r, euler, c2)
    assert dry == pytest.approx(c2 * euler * 0.5 * rho * v_max**2 * n_r)
    gamma_m = 0.02
    d_o = 0.01905
    wet, record = wet_pressure_drop(dry, gamma_m, d_o)
    factor = 1.0 + 0.5 * (gamma_m / d_o) / GAMMA_REF
    assert GAMMA_REF == pytest.approx((0.195 + 5.556) / 2.0)
    assert wet == pytest.approx(dry * factor)
    assert record.name == "湿工况管束压降修正"


def test_colebrook_matches_an_independent_root():
    reynolds = 1.0e5
    diameter = 0.1
    roughness = 1.0e-4

    def residual(value):
        return 1.0 / math.sqrt(value) + 2.0 * math.log10(
            roughness / (3.7 * diameter) + 2.51 / (reynolds * math.sqrt(value))
        )

    factor, record = darcy_friction_factor(reynolds, roughness, diameter)
    root = brentq(residual, 1.0e-4, 0.1)
    assert factor == pytest.approx(root, abs=COLEBROOK_TOLERANCE)
    assert abs(residual(factor)) < 1.0e-6
    again = 1.0 / (
        -2.0
        * math.log10(
            roughness / (3.7 * diameter) + 2.51 / (reynolds * math.sqrt(factor))
        )
    ) ** 2
    assert abs(again - factor) < COLEBROOK_TOLERANCE
    assert record.parameters[-1][0] == "lambda"
    smooth, _ = darcy_friction_factor(reynolds, 0.0, diameter)
    assert abs(residual_smooth(smooth, reynolds, diameter)) < 1.0e-6
    with pytest.raises(OutOfRangeError):
        darcy_friction_factor(0.0, roughness, diameter)


def residual_smooth(value, reynolds, diameter):
    return 1.0 / math.sqrt(value) + 2.0 * math.log10(
        2.51 / (reynolds * math.sqrt(value))
    )


def test_makeup_uses_spray_as_the_drift_base():
    tube = _tube()
    gamma = 0.0381
    result = evaluate_auxiliary(
        tube,
        2.0,
        gamma,
        1.2,
        1.8e-5,
        1000.0,
        0.001,
        1.5,
        0.01,
        0.015,
        _aux(drift_rate=0.02, N_cyc=3.0),
    )
    spray = gamma * 2.0 * tube.N_t * tube.L
    evaporated = 1.5 * (0.015 - 0.01)
    assert result.spray_mass_flow == pytest.approx(spray)
    assert result.m_evap == pytest.approx(evaporated)
    assert result.m_blowdown == pytest.approx(evaporated / 2.0)
    assert result.m_drift == pytest.approx(0.02 * spray)
    assert result.m_drift != pytest.approx(0.02 * 1.5)
    assert result.m_makeup == pytest.approx(
        result.m_evap + result.m_blowdown + result.m_drift
    )


def test_fan_and_pump_assemble_the_specified_terms():
    tube = _tube()
    aux = _aux()
    v_face = 2.0
    rho_air = 1.2
    rho_water = 1000.0
    result = evaluate_auxiliary(
        tube,
        v_face,
        0.0381,
        rho_air,
        1.8e-5,
        rho_water,
        0.001,
        1.5,
        0.01,
        0.015,
        aux,
    )
    assert result.air_volume_flow == pytest.approx(v_face * face_area(tube))
    accessory = (aux.zeta_de + aux.zeta_lv + aux.zeta_st) * rho_air * v_face**2 / 2.0
    assert result.delta_p_accessories == pytest.approx(accessory)
    assert result.fan_pressure == pytest.approx(result.delta_p_wet + accessory)
    assert result.fan_power == pytest.approx(
        result.air_volume_flow * result.fan_pressure / aux.eta_fan
    )
    ratio = (0.0381 / tube.S_T) / GAMMA_REF
    assert result.delta_p_wet == pytest.approx(result.delta_p_dry * (1.0 + 0.5 * ratio))
    area = math.pi * aux.pipe_diameter**2 / 4.0
    velocity = result.pump_volume_flow / area
    head = velocity**2 / (2.0 * STANDARD_GRAVITY)
    expected_head = (
        aux.p_noz / (rho_water * STANDARD_GRAVITY)
        + aux.H_lift
        + result.darcy_lambda * (aux.pipe_length / aux.pipe_diameter) * head
        + aux.zeta_pipe * head
    )
    assert result.pump_head == pytest.approx(expected_head)
    assert result.pump_power == pytest.approx(
        result.spray_mass_flow * STANDARD_GRAVITY * result.pump_head / aux.eta_pump
    )
    assert result.estimated_wet_correction is True
    assert [item.name for item in result.correlations] == [
        "Zukauskas–Ulinskas 错列光管欧拉数",
        "管排修正 C_2",
        "湿工况管束压降修正",
        "Colebrook–White Darcy λ",
    ]
    text = "\n".join(result.diagnostics)
    assert ZUKAUSKAS_BASIS_NOTE in text
    assert EQUILATERAL_K1_NOTE in text
    assert WET_ESTIMATE_NOTE in text
    assert "此为工程取值，非标准强制条款" in text
    assert DRIFT_ENGINEERING_NOTE in text
    assert result.warnings == ()


def test_defaults_and_rejected_inputs():
    aux = _aux()
    assert aux.eta_fan == 0.65
    assert aux.eta_pump == 0.70
    assert aux.N_cyc == 3.0
    assert aux.drift_rate == 0.0001
    with pytest.raises(OutOfRangeError) as cycles:
        _aux(N_cyc=1.0)
    assert cycles.value.param == "N_cyc"
    with pytest.raises(OutOfRangeError):
        _aux(eta_fan=1.2)
    tube = _tube()
    with pytest.raises(InputError):
        evaluate_auxiliary(
            tube, 0.0, 0.0381, 1.2, 1.8e-5, 1000.0, 0.001, 1.5, 0.01, 0.015, aux
        )
    with pytest.raises(OutOfRangeError) as slow:
        evaluate_auxiliary(
            tube, 1.0e-8, 0.0381, 1.2, 1.8e-5, 1000.0, 0.001, 1.5, 0.01, 0.015, aux
        )
    assert slow.value.param == "Re_max"
    low_fin = TubeGeometry(
        surface_type="tube_lowfin",
        d_o=0.01905,
        wall_thickness=0.002,
        k_w=63.9,
        S_T=0.04,
        S_L=0.03,
        N_r=4,
        N_t=1,
        L=2.0,
        fin_height=0.0015,
        fin_pitch=0.001,
        fin_thickness=0.0003,
    )
    with pytest.raises(UnconfirmedCorrelationError) as low_fin_error:
        evaluate_auxiliary(
            low_fin, 2.0, 0.0381, 1.2, 1.8e-5, 1000.0, 0.001, 1.5, 0.01, 0.015, aux
        )
    assert str(low_fin_error.value) == UNSUPPORTED_SURFACE_MESSAGE
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
        evaluate_auxiliary(
            plate, 2.0, 0.0381, 1.2, 1.8e-5, 1000.0, 0.001, 1.5, 0.01, 0.015, aux
        )
